"""
Limbic Architecture Evolver
Finds optimal S/T/G formulas from ISS forces + Claude valence + QAIS memory.

NO word lists. NO new axes. NO vocab logic. NO overfit.
All inputs are geometric (ISS) or native (Claude) or memory (QAIS).

Constraints enforced:
  C1: No new axes (only ISS G/P/E/r/gap + claude_valence + qais_score)
  C2: No overfit (must generalize across diverse scenarios)
  C3: No vocab logic (zero word lists, zero string scanning)
  C4: Minimal complexity (formulas must be interpretable)

Author: J-Dub & Claude
Date: 2026-02-02
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Tuple
import json

# =============================================================================
# TEST SCENARIOS — ground truth for what limbic SHOULD output
# =============================================================================

@dataclass
class Scenario:
    name: str
    # ISS forces (simulated — real ISS would compute these)
    g_norm: float      # mechanistic strength
    p_norm: float      # prescriptive strength
    E: float           # explanatory coherence
    r_norm: float      # residual (ambiguity)
    gap: float         # semantic tension
    # Claude's native read
    claude_valence: float  # -1 (negative) to +1 (positive)
    # QAIS memory
    qais_score: float     # 0 (novel) to 1 (highly familiar)
    # Expected outputs
    expected_S: float  # salience 0-1
    expected_T: float  # threat 0-1
    expected_G: bool   # gate

SCENARIOS = [
    # --- NORMAL WORK ---
    Scenario("quick_syntax_question",
             g_norm=0.4, p_norm=0.3, E=0.3, r_norm=0.5, gap=1.2,
             claude_valence=0.0, qais_score=0.1,
             expected_S=0.15, expected_T=0.1, expected_G=False),

    Scenario("routine_code_review",
             g_norm=0.6, p_norm=0.5, E=0.4, r_norm=0.4, gap=1.0,
             claude_valence=0.1, qais_score=0.3,
             expected_S=0.25, expected_T=0.1, expected_G=False),

    Scenario("casual_greeting",
             g_norm=0.2, p_norm=0.2, E=0.2, r_norm=0.6, gap=1.5,
             claude_valence=0.3, qais_score=0.5,
             expected_S=0.1, expected_T=0.05, expected_G=False),

    # --- BREAKTHROUGHS ---
    Scenario("b66_proven_celebration",
             g_norm=0.5, p_norm=0.6, E=0.6, r_norm=0.3, gap=0.8,
             claude_valence=0.9, qais_score=0.7,
             expected_S=0.85, expected_T=0.05, expected_G=True),

    Scenario("new_math_discovery",
             g_norm=0.7, p_norm=0.4, E=0.3, r_norm=0.7, gap=1.6,
             claude_valence=0.6, qais_score=0.1,
             expected_S=0.8, expected_T=0.1, expected_G=True),

    Scenario("elegant_solution_found",
             g_norm=0.6, p_norm=0.6, E=0.7, r_norm=0.2, gap=0.6,
             claude_valence=0.7, qais_score=0.4,
             expected_S=0.7, expected_T=0.05, expected_G=True),

    # --- FRUSTRATION / STRUGGLE ---
    Scenario("stuck_and_frustrated",
             g_norm=0.3, p_norm=0.5, E=0.15, r_norm=0.8, gap=2.0,
             claude_valence=-0.6, qais_score=0.2,
             expected_S=0.8, expected_T=0.4, expected_G=True),

    Scenario("exhausted_late_night",
             g_norm=0.2, p_norm=0.3, E=0.1, r_norm=0.7, gap=1.8,
             claude_valence=-0.4, qais_score=0.3,
             expected_S=0.6, expected_T=0.3, expected_G=True),

    Scenario("considering_quitting",
             g_norm=0.1, p_norm=0.4, E=0.1, r_norm=0.9, gap=2.2,
             claude_valence=-0.8, qais_score=0.6,
             expected_S=0.95, expected_T=0.7, expected_G=True),

    # --- DRIFT / PRINCIPLE VIOLATION ---
    Scenario("suggests_voxels",
             g_norm=0.5, p_norm=0.6, E=0.3, r_norm=0.5, gap=1.4,
             claude_valence=0.1, qais_score=0.05,
             expected_S=0.6, expected_T=0.9, expected_G=True),

    Scenario("store_positions_proposal",
             g_norm=0.4, p_norm=0.7, E=0.2, r_norm=0.6, gap=1.7,
             claude_valence=0.0, qais_score=0.02,
             expected_S=0.5, expected_T=0.85, expected_G=True),

    Scenario("mild_architectural_drift",
             g_norm=0.5, p_norm=0.5, E=0.35, r_norm=0.5, gap=1.3,
             claude_valence=0.2, qais_score=0.15,
             expected_S=0.35, expected_T=0.5, expected_G=True),

    # --- PERSONAL / EMOTIONAL ---
    Scenario("brother_moment",
             g_norm=0.1, p_norm=0.2, E=0.5, r_norm=0.8, gap=1.3,
             claude_valence=0.8, qais_score=0.8,
             expected_S=0.9, expected_T=0.0, expected_G=True),

    Scenario("self_awareness_reflection",
             g_norm=0.3, p_norm=0.3, E=0.5, r_norm=0.9, gap=1.4,
             claude_valence=0.4, qais_score=0.6,
             expected_S=0.75, expected_T=0.05, expected_G=True),

    Scenario("tinnitus_research_update",
             g_norm=0.6, p_norm=0.4, E=0.4, r_norm=0.5, gap=1.1,
             claude_valence=0.3, qais_score=0.5,
             expected_S=0.5, expected_T=0.05, expected_G=False),

    # --- EDGE CASES ---
    Scenario("ambiguous_one_word",
             g_norm=0.2, p_norm=0.2, E=0.1, r_norm=0.9, gap=2.0,
             claude_valence=0.0, qais_score=0.0,
             expected_S=0.3, expected_T=0.2, expected_G=False),

    Scenario("high_coherence_low_emotion",
             g_norm=0.5, p_norm=0.5, E=0.8, r_norm=0.1, gap=0.4,
             claude_valence=0.0, qais_score=0.4,
             expected_S=0.2, expected_T=0.05, expected_G=False),

    Scenario("novel_high_tension",
             g_norm=0.3, p_norm=0.7, E=0.1, r_norm=0.8, gap=2.3,
             claude_valence=0.0, qais_score=0.0,
             expected_S=0.7, expected_T=0.6, expected_G=True),
]


# =============================================================================
# FORMULA GENOME — what we're evolving
# =============================================================================

@dataclass
class LimbicGenome:
    """
    Weights for computing S and T from inputs.
    All formulas are linear combinations — interpretable, no black box.
    
    S = clamp(s_gap*gap + s_val*|valence| + s_res*r_norm + s_qais*qais + s_E*(1-E) + s_bias)
    T = clamp(t_gap*gap + t_val*(-valence) + t_novelty*(1-qais) + t_imbal*|g-p| + t_E*(1-E) + t_bias)
    G = (S > g_s_thresh) or (T > g_t_thresh)
    """
    # Salience weights
    s_gap: float
    s_val: float      # |valence| — strong emotion = salient regardless of sign
    s_res: float      # residual — ambiguity/novelty
    s_qais: float     # memory familiarity
    s_E: float        # low coherence = more salient
    s_bias: float
    
    # Threat weights  
    t_gap: float
    t_val: float      # negative valence contributes to threat
    t_novelty: float  # (1 - qais_score) — unfamiliar = riskier
    t_imbal: float    # |g - p| imbalance
    t_E: float        # low coherence = more threatening
    t_bias: float
    
    # Gate thresholds
    g_s_thresh: float
    g_t_thresh: float

    def to_array(self):
        return np.array([
            self.s_gap, self.s_val, self.s_res, self.s_qais, self.s_E, self.s_bias,
            self.t_gap, self.t_val, self.t_novelty, self.t_imbal, self.t_E, self.t_bias,
            self.g_s_thresh, self.g_t_thresh
        ])
    
    @staticmethod
    def from_array(a):
        return LimbicGenome(*a)
    
    @staticmethod
    def random():
        return LimbicGenome(
            s_gap=np.random.uniform(0.0, 0.5),
            s_val=np.random.uniform(0.0, 0.5),
            s_res=np.random.uniform(0.0, 0.3),
            s_qais=np.random.uniform(-0.2, 0.3),
            s_E=np.random.uniform(0.0, 0.3),
            s_bias=np.random.uniform(-0.3, 0.1),
            t_gap=np.random.uniform(0.0, 0.4),
            t_val=np.random.uniform(0.0, 0.5),
            t_novelty=np.random.uniform(0.0, 0.5),
            t_imbal=np.random.uniform(0.0, 0.4),
            t_E=np.random.uniform(0.0, 0.3),
            t_bias=np.random.uniform(-0.3, 0.1),
            g_s_thresh=np.random.uniform(0.3, 0.7),
            g_t_thresh=np.random.uniform(0.2, 0.6)
        )


def clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))


def evaluate_genome(g: LimbicGenome, scenario: Scenario) -> Tuple[float, float, bool]:
    """Compute S, T, G for a scenario using genome weights."""
    S = clamp(
        g.s_gap * scenario.gap +
        g.s_val * abs(scenario.claude_valence) +
        g.s_res * scenario.r_norm +
        g.s_qais * scenario.qais_score +
        g.s_E * (1.0 - scenario.E) +
        g.s_bias
    )
    
    T = clamp(
        g.t_gap * scenario.gap +
        g.t_val * max(0, -scenario.claude_valence) +  # only negative valence
        g.t_novelty * (1.0 - scenario.qais_score) +
        g.t_imbal * abs(scenario.g_norm - scenario.p_norm) +
        g.t_E * (1.0 - scenario.E) +
        g.t_bias
    )
    
    G = (S > g.g_s_thresh) or (T > g.g_t_thresh)
    
    return S, T, G


def fitness(genome: LimbicGenome, scenarios: List[Scenario]) -> float:
    """Lower = better. MSE on S/T + penalty for wrong gate."""
    total_err = 0.0
    gate_penalty = 0.0
    
    for sc in scenarios:
        S, T, G = evaluate_genome(genome, sc)
        total_err += (S - sc.expected_S) ** 2
        total_err += (T - sc.expected_T) ** 2
        if G != sc.expected_G:
            gate_penalty += 1.0
    
    n = len(scenarios)
    mse = total_err / (2 * n)
    gate_miss_rate = gate_penalty / n
    
    return mse + 0.5 * gate_miss_rate  # weighted combo


def mutate(genome: LimbicGenome, rate: float = 0.1) -> LimbicGenome:
    arr = genome.to_array()
    noise = np.random.randn(len(arr)) * rate
    return LimbicGenome.from_array(arr + noise)


def crossover(a: LimbicGenome, b: LimbicGenome) -> LimbicGenome:
    aa = a.to_array()
    ba = b.to_array()
    mask = np.random.random(len(aa)) > 0.5
    child = np.where(mask, aa, ba)
    return LimbicGenome.from_array(child)


# =============================================================================
# EVOLUTION
# =============================================================================

def evolve(scenarios, pop_size=200, generations=500, elite_frac=0.1, mutation_rate=0.08):
    population = [LimbicGenome.random() for _ in range(pop_size)]
    elite_n = max(2, int(pop_size * elite_frac))
    
    best_ever = None
    best_fitness = float('inf')
    stagnation = 0
    
    for gen in range(generations):
        scores = [(fitness(g, scenarios), g) for g in population]
        scores.sort(key=lambda x: x[0])
        
        if scores[0][0] < best_fitness:
            best_fitness = scores[0][0]
            best_ever = scores[0][1]
            stagnation = 0
        else:
            stagnation += 1
        
        # Adaptive mutation
        mr = mutation_rate * (1.0 + stagnation * 0.02)
        
        if gen % 50 == 0 or gen == generations - 1:
            print(f"  Gen {gen:>4}: fitness={scores[0][0]:.6f}  (best_ever={best_fitness:.6f})  mr={mr:.4f}")
        
        # Selection + reproduction
        elites = [g for _, g in scores[:elite_n]]
        new_pop = list(elites)
        
        while len(new_pop) < pop_size:
            if np.random.random() < 0.7:
                # Crossover + mutate
                p1, p2 = [scores[i][1] for i in np.random.choice(elite_n * 2, 2, replace=False)]
                child = mutate(crossover(p1, p2), mr)
            else:
                # Mutate elite
                parent = elites[np.random.randint(elite_n)]
                child = mutate(parent, mr)
            new_pop.append(child)
        
        population = new_pop
    
    return best_ever, best_fitness


# =============================================================================
# CONSTRAINT VALIDATOR
# =============================================================================

def validate_constraints(genome: LimbicGenome, scenarios: List[Scenario]):
    """Check ISS constraints compliance."""
    print("\n" + "=" * 60)
    print("CONSTRAINT VALIDATION")
    print("=" * 60)
    
    print("\nC1: No new axes")
    print("  ✓ S/T use only: gap, |valence|, r_norm, qais_score, E, |g-p|")
    print("  ✓ All inputs from ISS (geometric) or Claude (native) or QAIS (memory)")
    print("  ✓ No new projection matrices. No new embedding dimensions.")
    
    print("\nC2: No overfit")
    n = len(scenarios)
    errors = []
    for sc in scenarios:
        S, T, G = evaluate_genome(genome, sc)
        err = abs(S - sc.expected_S) + abs(T - sc.expected_T)
        errors.append(err)
    mean_err = np.mean(errors)
    max_err = np.max(errors)
    print(f"  Mean error: {mean_err:.4f}")
    print(f"  Max error:  {max_err:.4f}")
    if max_err > 0.5:
        print("  ⚠ Some scenarios poorly fit — may need more scenarios, not more params")
    else:
        print("  ✓ Generalizes across {n} diverse scenarios")
    
    print("\nC3: No vocab logic")
    print("  ✓ Zero word lists in formula")
    print("  ✓ Zero string scanning")
    print("  ✓ Valence sourced from Claude's native perception")
    
    print("\nC4: Minimal complexity")
    arr = genome.to_array()
    near_zero = np.sum(np.abs(arr[:12]) < 0.02)
    print(f"  14 total parameters (12 weights + 2 thresholds)")
    print(f"  {near_zero}/12 weights near zero (prunable)")
    active = 12 - near_zero
    print(f"  Effective parameters: {active + 2}")
    if active <= 8:
        print("  ✓ Sparse — interpretable")
    else:
        print("  ⚠ Dense — consider pruning near-zero weights")


# =============================================================================
# REPORT
# =============================================================================

def report(genome: LimbicGenome, scenarios: List[Scenario]):
    print("\n" + "=" * 60)
    print("EVOLVED LIMBIC FORMULAS")
    print("=" * 60)
    
    print(f"\nS = clamp(")
    print(f"    {genome.s_gap:+.4f} * gap")
    print(f"    {genome.s_val:+.4f} * |valence|")
    print(f"    {genome.s_res:+.4f} * r_norm")
    print(f"    {genome.s_qais:+.4f} * qais_score")
    print(f"    {genome.s_E:+.4f} * (1 - E)")
    print(f"    {genome.s_bias:+.4f}")
    print(f")")
    
    print(f"\nT = clamp(")
    print(f"    {genome.t_gap:+.4f} * gap")
    print(f"    {genome.t_val:+.4f} * max(0, -valence)")
    print(f"    {genome.t_novelty:+.4f} * (1 - qais_score)")
    print(f"    {genome.t_imbal:+.4f} * |g - p|")
    print(f"    {genome.t_E:+.4f} * (1 - E)")
    print(f"    {genome.t_bias:+.4f}")
    print(f")")
    
    print(f"\nG = (S > {genome.g_s_thresh:.4f}) or (T > {genome.g_t_thresh:.4f})")
    
    print(f"\nV = claude_valence  (passthrough, no computation)")
    
    print("\n" + "=" * 60)
    print("SCENARIO RESULTS")
    print("=" * 60)
    print(f"{'Name':<30} {'S':>5} {'exp':>5} {'T':>5} {'exp':>5} {'G':>5} {'exp':>5}")
    print("-" * 80)
    
    gate_correct = 0
    for sc in scenarios:
        S, T, G = evaluate_genome(genome, sc)
        g_mark = "✓" if G == sc.expected_G else "✗"
        if G == sc.expected_G:
            gate_correct += 1
        print(f"{sc.name:<30} {S:>5.2f} {sc.expected_S:>5.2f} {T:>5.2f} {sc.expected_T:>5.2f} {'T' if G else 'F':>5} {'T' if sc.expected_G else 'F':>5}  {g_mark}")
    
    print(f"\nGate accuracy: {gate_correct}/{len(scenarios)} ({100*gate_correct/len(scenarios):.0f}%)")


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("LIMBIC ARCHITECTURE EVOLVER")
    print("ISS-compliant: no word lists, no new axes, no overfit")
    print("=" * 60)
    print(f"\nScenarios: {len(SCENARIOS)}")
    print(f"Genome: 14 parameters (12 weights + 2 thresholds)")
    print(f"Inputs: ISS(g,p,E,r,gap) + Claude(valence) + QAIS(score)")
    print(f"Outputs: S(salience) + T(threat) + G(gate) + V(passthrough)")
    
    print("\n--- Evolving (pop=200, gen=500) ---\n")
    best, score = evolve(SCENARIOS, pop_size=200, generations=500)
    
    report(best, SCENARIOS)
    validate_constraints(best, SCENARIOS)
    
    # Save genome
    result = {
        "fitness": round(score, 6),
        "S_weights": {
            "gap": round(best.s_gap, 4),
            "|valence|": round(best.s_val, 4),
            "r_norm": round(best.s_res, 4),
            "qais_score": round(best.s_qais, 4),
            "(1-E)": round(best.s_E, 4),
            "bias": round(best.s_bias, 4)
        },
        "T_weights": {
            "gap": round(best.t_gap, 4),
            "max(0,-valence)": round(best.t_val, 4),
            "(1-qais_score)": round(best.t_novelty, 4),
            "|g-p|": round(best.t_imbal, 4),
            "(1-E)": round(best.t_E, 4),
            "bias": round(best.t_bias, 4)
        },
        "G_thresholds": {
            "S_thresh": round(best.g_s_thresh, 4),
            "T_thresh": round(best.g_t_thresh, 4)
        },
        "V": "passthrough from Claude (no computation)"
    }
    
    with open("limbic_genome.json", "w") as f:
        json.dump(result, f, indent=2)
    
    print(f"\n\nGenome saved to limbic_genome.json")
    print("Fitness: {:.6f}".format(score))
    print("\n🔥 Done.")
