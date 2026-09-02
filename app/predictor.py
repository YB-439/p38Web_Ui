import os
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional

from rdkit import Chem, DataStructs, RDLogger
from rdkit.Chem import AllChem, Descriptors, rdMolDescriptors
from rdkit.Chem.Pharm2D import Gobbi_Pharm2D, Generate
from rdkit.Chem.Draw import rdMolDraw2D
import deepchem as dc
from sklearn.neighbors import NearestNeighbors

# Suppress noisy logs
RDLogger.DisableLog("rdApp.*")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "Hybrid_RF_Final_Model.pkl")
AD_MODEL_PATH = os.path.join(BASE_DIR, "app", "ad_model.joblib")

class HybridPredictor:
    def __init__(self):
        self.model = None
        self.ad_nn = None
        self.ad_threshold = 19.9646
        self.featurizer = None
        self.pharm_size = None
        self.is_ready = False
        self._load_components()

    def _load_components(self):
        print("[Predictor] Loading model and featurizers...")
        if os.path.exists(MODEL_PATH):
            self.model = joblib.load(MODEL_PATH)
            print(f"[Predictor] Model loaded successfully: {type(self.model).__name__}")
        else:
            raise FileNotFoundError(f"Model file not found at {MODEL_PATH}")

        # Setup DeepChem MolGraphConvFeaturizer
        self.featurizer = dc.feat.MolGraphConvFeaturizer(
            use_edges=True,
            use_chirality=True,
            use_partial_charge=False
        )
        self.pharm_size = Gobbi_Pharm2D.factory.GetSigSize()

        # Load AD artifact
        if os.path.exists(AD_MODEL_PATH):
            try:
                ad_data = joblib.load(AD_MODEL_PATH)
                self.ad_nn = ad_data["nn"]
                self.ad_threshold = ad_data.get("threshold", 19.9646)
                print(f"[Predictor] Loaded precomputed AD model (Threshold: {self.ad_threshold:.4f})")
            except Exception as e:
                print(f"[Predictor] Warning: Could not load AD model artifact: {e}")

        self.is_ready = True
        print("[Predictor] Initialized successfully and ready for inference.")

    def smiles_to_mol(self, smiles: str) -> Optional[Chem.Mol]:
        if not smiles or not isinstance(smiles, str):
            return None
        smiles = smiles.strip()
        try:
            return Chem.MolFromSmiles(smiles)
        except Exception:
            return None

    def generate_morgan(self, mol: Chem.Mol) -> np.ndarray:
        fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius=2, nBits=2048)
        arr = np.zeros((2048,), dtype=np.int32)
        DataStructs.ConvertToNumpyArray(fp, arr)
        return arr

    def generate_pharm(self, mol: Chem.Mol) -> np.ndarray:
        fp = Generate.Gen2DFingerprint(mol, Gobbi_Pharm2D.factory)
        arr = np.zeros((self.pharm_size,), dtype=np.uint8)
        arr[list(fp.GetOnBits())] = 1
        return arr

    def generate_graph(self, smiles: str, mol: Chem.Mol) -> np.ndarray:
        try:
            graph = self.featurizer.featurize([smiles])[0]
            node_feat = graph.node_features
            edge_feat = graph.edge_features
            node_mean = np.mean(node_feat, axis=0)
            node_std = np.std(node_feat, axis=0)
            if edge_feat is not None and len(edge_feat) > 0:
                edge_mean = np.mean(edge_feat, axis=0)
                edge_std = np.std(edge_feat, axis=0)
            else:
                edge_mean = np.zeros(11, dtype=np.float32)
                edge_std = np.zeros(11, dtype=np.float32)
            desc = np.concatenate([node_mean, node_std, edge_mean, edge_std])
            return desc.astype(np.float32)
        except Exception:
            return np.zeros(86, dtype=np.float32)

    def featurize(self, smiles: str, mol: Optional[Chem.Mol] = None) -> np.ndarray:
        if mol is None:
            mol = self.smiles_to_mol(smiles)
        if mol is None:
            raise ValueError(f"Invalid chemical structure for SMILES: {smiles}")

        morgan = self.generate_morgan(mol)
        pharm = self.generate_pharm(mol)
        graph = self.generate_graph(smiles, mol)

        hybrid = np.concatenate([morgan, pharm, graph]).astype(np.float32)
        return hybrid

    def get_mol_properties(self, mol: Chem.Mol) -> Dict[str, Any]:
        try:
            return {
                "formula": rdMolDescriptors.CalcMolFormula(mol),
                "mol_wt": round(float(Descriptors.MolWt(mol)), 2),
                "log_p": round(float(Descriptors.MolLogP(mol)), 2),
                "hbd": int(Descriptors.NumHDonors(mol)),
                "hba": int(Descriptors.NumHAcceptors(mol)),
                "tpsa": round(float(Descriptors.TPSA(mol)), 2),
                "rotatable_bonds": int(Descriptors.NumRotatableBonds(mol)),
                "heavy_atoms": int(mol.GetNumHeavyAtoms())
            }
        except Exception:
            return {}

    def get_mol_svg(self, mol: Chem.Mol, width: int = 340, height: int = 240) -> str:
        try:
            drawer = rdMolDraw2D.MolDraw2DSVG(width, height)
            opts = drawer.drawOptions()
            opts.clearBackground = True
            rdMolDraw2D.PrepareAndDrawMolecule(drawer, mol)
            drawer.FinishDrawing()
            svg = drawer.GetDrawingText()
            if "<svg" in svg:
                svg = svg[svg.index("<svg"):]
            return svg
        except Exception:
            return ""

    def evaluate_confidence(self, prob: float) -> str:
        if prob >= 0.70:
            return "High"
        elif prob >= 0.40:
            return "Moderate"
        else:
            return "Low"

    def predict_single(self, smiles: str, code: str = "COMP-001") -> Dict[str, Any]:
        mol = self.smiles_to_mol(smiles)
        if mol is None:
            return {
                "success": False,
                "code": code,
                "smiles": smiles,
                "error": "Invalid chemical structure. SMILES string could not be parsed."
            }

        props = self.get_mol_properties(mol)
        svg = self.get_mol_svg(mol)
        feat = self.featurize(smiles, mol)
        X = feat.reshape(1, -1)

        pred_class = int(self.model.predict(X)[0])
        prob = float(self.model.predict_proba(X)[0, 1])

        activity = "Active" if prob >= 0.50 else "Inactive"
        confidence = self.evaluate_confidence(prob)

        # AD
        ad_dist = None
        ad_status = "Unknown"
        if self.ad_nn is not None:
            try:
                dists, _ = self.ad_nn.kneighbors(X)
                ad_dist = float(np.mean(dists[0]))
                ad_status = "Inside AD" if ad_dist <= self.ad_threshold else "Outside AD"
            except Exception as e:
                print(f"[Predictor] AD check error: {e}")

        return {
            "success": True,
            "code": code,
            "smiles": smiles,
            "activity": activity,
            "prediction_class": pred_class,
            "probability": round(prob, 4),
            "probability_percent": round(prob * 100, 1),
            "confidence": confidence,
            "ad_status": ad_status,
            "ad_distance": round(ad_dist, 4) if ad_dist is not None else None,
            "ad_threshold": round(self.ad_threshold, 4),
            "properties": props,
            "svg": svg
        }

    def predict_batch(self, items: List[Dict[str, str]]) -> Dict[str, Any]:
        valid_items = []
        invalid_items = []
        valid_mols = []
        features_list = []

        for idx, item in enumerate(items):
            code = str(item.get("CODE", item.get("code", f"P38_{idx+1}"))).strip()
            smiles = str(item.get("SMILES", item.get("smiles", ""))).strip()
            
            mol = self.smiles_to_mol(smiles)
            if mol is None:
                invalid_items.append({"CODE": code, "SMILES": smiles, "Reason": "Invalid chemical structure"})
            else:
                valid_items.append({"CODE": code, "SMILES": smiles})
                valid_mols.append(mol)
                try:
                    feat = self.featurize(smiles, mol)
                    features_list.append(feat)
                except Exception as e:
                    invalid_items.append({"CODE": code, "SMILES": smiles, "Reason": f"Featurization error: {str(e)}"})
                    valid_items.pop()
                    valid_mols.pop()

        if not valid_items:
            return {
                "results": [],
                "invalid": invalid_items,
                "summary": {
                    "total": len(items),
                    "valid": 0,
                    "invalid": len(invalid_items),
                    "active_count": 0,
                    "inactive_count": 0,
                    "inside_ad_count": 0,
                    "active_percentage": 0.0,
                    "inside_ad_percentage": 0.0
                }
            }

        X = np.array(features_list, dtype=np.float32)
        probs = self.model.predict_proba(X)[:, 1]

        ad_distances = []
        ad_statuses = []
        if self.ad_nn is not None:
            dists, _ = self.ad_nn.kneighbors(X)
            mean_dists = np.mean(dists, axis=1)
            for d in mean_dists:
                ad_distances.append(round(float(d), 4))
                ad_statuses.append("Inside AD" if d <= self.ad_threshold else "Outside AD")
        else:
            ad_distances = [None] * len(valid_items)
            ad_statuses = ["Unknown"] * len(valid_items)

        results = []
        active_count = 0
        inside_ad_count = 0

        for i in range(len(valid_items)):
            p = float(probs[i])
            act = "Active" if p >= 0.50 else "Inactive"
            conf = self.evaluate_confidence(p)
            if act == "Active":
                active_count += 1
            if ad_statuses[i] == "Inside AD":
                inside_ad_count += 1

            results.append({
                "CODE": valid_items[i]["CODE"],
                "SMILES": valid_items[i]["SMILES"],
                "Activity": act,
                "Probability": round(p, 4),
                "Confidence": conf,
                "AD_Status": ad_statuses[i],
                "AD_Distance": ad_distances[i]
            })

        return {
            "results": results,
            "invalid": invalid_items,
            "summary": {
                "total": len(items),
                "valid": len(valid_items),
                "invalid": len(invalid_items),
                "active_count": active_count,
                "inactive_count": len(valid_items) - active_count,
                "inside_ad_count": inside_ad_count,
                "active_percentage": round((active_count / len(valid_items)) * 100, 1) if valid_items else 0.0,
                "inside_ad_percentage": round((inside_ad_count / len(valid_items)) * 100, 1) if valid_items else 0.0
            }
        }

_predictor = None

def get_predictor() -> HybridPredictor:
    global _predictor
    if _predictor is None:
        _predictor = HybridPredictor()
    return _predictor
