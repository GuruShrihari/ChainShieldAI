/**
 * ⚠️ MOCK DATA — These values will be replaced by real ML model outputs in a future sprint.
 * Do NOT use these for any real analysis. Placeholder only.
 */

export const MOCK_CASHOUT_PROBABILITIES: Record<string, number> = {
    // Keyed by chain path string e.g. "ACC_001->ACC_012->ACC_034"
    // Values are hardcoded realistic-looking floats
    'ACC_001->ACC_012->ACC_034': 0.72,
    'ACC_005->ACC_018->ACC_042': 0.65,
    'ACC_010->ACC_023->ACC_037->ACC_049': 0.81,
    'ACC_003->ACC_017->ACC_029': 0.58,
    'ACC_008->ACC_031->ACC_045->ACC_050': 0.89,
};

// ⚠️ MOCK — Will be model.predict_proba() output
export const MOCK_MODEL_CONFIDENCE = 0.0;

// ⚠️ MOCK — Model status placeholder
export const MOCK_MODEL_STATUS = {
    status: 'pending' as const,
    version: null as string | null,
    accuracy: null as number | null,
    message: 'ML model integration coming soon',
};

/**
 * ⚠️ MOCK — Returns a deterministic mock value based on chain length.
 * Replace with API call to backend ML endpoint when ready.
 */
export function getMockCashoutProbability(chainPath: string[]): number {
    const base = 0.3 + chainPath.length * 0.1;
    return Math.min(base + (chainPath.length % 3) * 0.07, 0.95);
}
