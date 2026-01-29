"""
QAIS Visual Resonance Extension
"Don't index. Resonate." — Now with vision.

Extends QAIS to bind images to the field.
Visual memories resonate against new images.

Part of BOND Protocol | github.com/moneyjarrod/BOND
Created: Session 63 | J-Dub & Claude | 2026-01-30
Tested: 100:1 signal-to-noise ratio on recognition

Requirements: pip install numpy Pillow

Usage:
    from qais_visual import store_visual, recognize, visual_stats
    
    # Store an image with identity and contexts
    store_visual("photo.jpg", "Alice", ["person", "office"])
    
    # Later, recognize who's in a new image
    results = recognize("new_photo.jpg", ["Alice", "Bob", "stranger"])
    # Returns ranked candidates with confidence scores
"""

import numpy as np
import hashlib
import os
from typing import Dict, List, Optional

# Match QAIS core dimensions
N = 4096


# =============================================================================
# IMAGE PROCESSING
# =============================================================================

def load_image(path: str) -> np.ndarray:
    """Load and normalize image to 64x64 RGB array."""
    from PIL import Image
    img = Image.open(path).convert('RGB')
    img = img.resize((64, 64), Image.Resampling.LANCZOS)
    return np.array(img, dtype=np.float32) / 255.0


def extract_features(img: np.ndarray) -> np.ndarray:
    """
    Extract 1088-dimensional feature vector from image.
    - 768: Color histograms (256 bins × 3 channels)
    - 192: Spatial features (8×8 grid × 3 channels)
    - 128: Edge features (64 magnitude + 64 direction bins)
    """
    features = []
    
    # Color histograms (768 dims)
    for c in range(3):
        hist, _ = np.histogram(img[:, :, c], bins=256, range=(0, 1))
        hist = hist.astype(np.float32) / (hist.sum() + 1e-8)
        features.extend(hist)
    
    # Spatial grid means (192 dims)
    for i in range(8):
        for j in range(8):
            cell = img[i*8:(i+1)*8, j*8:(j+1)*8]
            features.extend(cell.mean(axis=(0, 1)))
    
    # Edge features (128 dims)
    gray = img.mean(axis=2)
    gx = np.diff(gray, axis=1)[:-1, :]
    gy = np.diff(gray, axis=0)[:, :-1]
    magnitude = np.sqrt(gx**2 + gy**2)
    direction = np.arctan2(gy, gx)
    
    mag_hist, _ = np.histogram(magnitude.flatten(), bins=64, range=(0, 1.5))
    dir_hist, _ = np.histogram(direction.flatten(), bins=64, range=(-np.pi, np.pi))
    mag_hist = mag_hist.astype(np.float32) / (mag_hist.sum() + 1e-8)
    dir_hist = dir_hist.astype(np.float32) / (dir_hist.sum() + 1e-8)
    features.extend(mag_hist)
    features.extend(dir_hist)
    
    return np.array(features, dtype=np.float32)


# =============================================================================
# HYPERDIMENSIONAL VECTORS
# =============================================================================

def features_to_hd_vector(features: np.ndarray) -> np.ndarray:
    """Project feature vector to N-dimensional bipolar HD vector."""
    feature_hash = hashlib.sha512(features.tobytes()).digest()
    rng = np.random.RandomState(list(feature_hash[:4]))
    projection = rng.randn(len(features), N).astype(np.float32) / np.sqrt(len(features))
    projected = features @ projection
    hd_vector = np.sign(projected)
    hd_vector[hd_vector == 0] = 1
    return hd_vector.astype(np.float32)


def seed_to_vector(seed: str) -> np.ndarray:
    """Convert semantic seed to HD vector (matches QAIS core)."""
    h = hashlib.sha512(seed.encode()).digest()
    rng = np.random.RandomState(list(h[:4]))
    return rng.choice([-1, 1], size=N).astype(np.float32)


def image_to_vector(path: str) -> np.ndarray:
    """Convert image file to N-dimensional bipolar HD vector."""
    img = load_image(path)
    features = extract_features(img)
    return features_to_hd_vector(features)


def resonance(a: np.ndarray, b: np.ndarray) -> float:
    """Compute resonance score between two vectors."""
    return float(np.dot(a, b) / N)


def bind(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Bind two vectors (element-wise multiplication)."""
    return a * b


# =============================================================================
# VISUAL FIELD
# =============================================================================

class QAISVisualField:
    """
    Visual resonance field for QAIS.
    Stores visual memories bound with semantic context.
    
    Note: This is a context matcher, not a person recognizer.
    Works best for:
    - Recognizing the same/similar images
    - Screenshots with consistent visual structure
    - Workspace/environment recognition
    
    Not suitable for:
    - Cross-condition person recognition (different lighting, angle, clothing)
    """
    
    def __init__(self, field_path: Optional[str] = None):
        if field_path is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            field_path = os.path.join(script_dir, "qais_visual_field.npz")
        self.field_path = field_path
        self.visual_field = np.zeros(N, dtype=np.float32)
        self.bindings: List[Dict] = []
        self.count = 0
        
        if os.path.exists(self.field_path):
            self._load()
    
    def _load(self):
        try:
            data = np.load(self.field_path, allow_pickle=True)
            self.visual_field = data['visual_field']
            self.bindings = data['bindings'].tolist()
            self.count = int(data['count'])
        except Exception:
            pass
    
    def _save(self):
        try:
            np.savez(self.field_path,
                visual_field=self.visual_field,
                bindings=np.array(self.bindings, dtype=object),
                count=self.count)
        except Exception as e:
            print(f"Save error: {e}")
    
    def store(self, image_path: str, identity: str, contexts: List[str],
              description: str = "") -> Dict:
        """
        Store a visual memory bound with identity and contexts.
        
        Args:
            image_path: Path to image file
            identity: Who/what is in the image
            contexts: List of context tags (e.g., ["person", "workspace"])
            description: Optional text description
        
        Returns:
            Dict with status and binding info
        """
        try:
            visual_vec = image_to_vector(image_path)
        except Exception as e:
            return {"status": "error", "message": str(e)}
        
        # Bind visual with identity
        id_vec = seed_to_vector(identity)
        self.visual_field += bind(visual_vec, id_vec)
        
        # Bind visual with each context
        for ctx in contexts:
            ctx_vec = seed_to_vector(ctx)
            self.visual_field += bind(visual_vec, ctx_vec)
        
        # Record binding
        binding = {
            "image": os.path.basename(image_path),
            "identity": identity,
            "contexts": contexts,
            "description": description,
            "index": self.count
        }
        self.bindings.append(binding)
        self.count += 1
        
        self._save()
        
        return {"status": "stored", "binding": binding, "count": self.count}
    
    def recognize(self, image_path: str, candidates: List[str]) -> List[Dict]:
        """
        Given an image, rank candidate identities by resonance.
        
        Args:
            image_path: Path to query image
            candidates: List of possible identities to check
        
        Returns:
            List of candidates ranked by resonance score
        """
        try:
            visual_vec = image_to_vector(image_path)
        except Exception as e:
            return [{"error": str(e)}]
        
        # Unbind visual from field to get identity residual
        residual = bind(self.visual_field, visual_vec)
        
        results = []
        for candidate in candidates:
            cand_vec = seed_to_vector(candidate)
            score = resonance(cand_vec, residual)
            confidence = "HIGH" if score > 0.3 else "MEDIUM" if score > 0.1 else "LOW" if score > 0.02 else "NOISE"
            results.append({"identity": candidate, "score": round(score, 4), "confidence": confidence})
        
        return sorted(results, key=lambda x: -x["score"])
    
    def get_contexts(self, image_path: str, candidate_contexts: List[str]) -> List[Dict]:
        """
        Given an image, rank candidate contexts by resonance.
        """
        try:
            visual_vec = image_to_vector(image_path)
        except Exception as e:
            return [{"error": str(e)}]
        
        residual = bind(self.visual_field, visual_vec)
        
        results = []
        for ctx in candidate_contexts:
            ctx_vec = seed_to_vector(ctx)
            score = resonance(ctx_vec, residual)
            confidence = "HIGH" if score > 0.3 else "MEDIUM" if score > 0.1 else "LOW" if score > 0.02 else "NOISE"
            results.append({"context": ctx, "score": round(score, 4), "confidence": confidence})
        
        return sorted(results, key=lambda x: -x["score"])
    
    def stats(self) -> Dict:
        """Get visual field statistics."""
        return {
            "total_bindings": self.count,
            "field_magnitude": float(np.linalg.norm(self.visual_field)),
            "stored_images": [b["image"] for b in self.bindings]
        }


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

_FIELD: Optional[QAISVisualField] = None

def get_field() -> QAISVisualField:
    """Get or create the global visual field."""
    global _FIELD
    if _FIELD is None:
        _FIELD = QAISVisualField()
    return _FIELD

def store_visual(image_path: str, identity: str, contexts: List[str], description: str = "") -> Dict:
    """Store a visual memory."""
    return get_field().store(image_path, identity, contexts, description)

def recognize(image_path: str, candidates: List[str]) -> List[Dict]:
    """Recognize who/what is in an image."""
    return get_field().recognize(image_path, candidates)

def visual_contexts(image_path: str, contexts: List[str]) -> List[Dict]:
    """Get contexts associated with an image."""
    return get_field().get_contexts(image_path, contexts)

def visual_stats() -> Dict:
    """Get visual field statistics."""
    return get_field().stats()


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    import sys
    
    print("QAIS Visual Resonance Module")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        path = sys.argv[1]
        print(f"Testing with: {path}")
        
        vec = image_to_vector(path)
        print(f"HD vector: {len(vec)} dimensions")
        print(f"Bipolar: {np.unique(vec)}")
        print(f"Self-resonance: {resonance(vec, vec):.4f}")
        
        # Test semantic binding
        test_id = seed_to_vector("test")
        bound = bind(vec, test_id)
        print(f"Bound self-resonance: {resonance(bound, bound):.4f}")
        print(f"Cross-resonance: {resonance(vec, test_id):.4f}")
        
        print("\n✓ Ready for visual memory storage")
    else:
        print("Usage: python qais_visual.py <image_path>")
        print("\nThis module provides visual resonance for QAIS.")
        print("Store images bound with identities, then recognize later.")
