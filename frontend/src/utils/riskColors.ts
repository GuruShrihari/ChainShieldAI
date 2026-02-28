/**
 * Risk color utilities for ChainShieldAI.
 *
 * Interpolates colors on a green→yellow→orange→red gradient
 * mapped to the 0-10 risk score scale.
 */

/**
 * Get the color for a risk score on a 0-10 scale.
 * Interpolates: green (0) → yellow (3.3) → orange (6.6) → red (10)
 */
export function getRiskColor(score: number): string {
    const clamped = Math.max(0, Math.min(10, score));
    const t = clamped / 10;

    if (t < 0.33) {
        // Green → Yellow
        const local = t / 0.33;
        const r = Math.round(0 + local * 255);
        const g = Math.round(255);
        const b = Math.round(136 - local * 136);
        return `rgb(${r}, ${g}, ${b})`;
    } else if (t < 0.66) {
        // Yellow → Orange
        const local = (t - 0.33) / 0.33;
        const r = 255;
        const g = Math.round(255 - local * 85);
        const b = Math.round(0);
        return `rgb(${r}, ${g}, ${b})`;
    } else {
        // Orange → Red
        const local = (t - 0.66) / 0.34;
        const r = 255;
        const g = Math.round(170 - local * 125);
        const b = Math.round(0 + local * 85);
        return `rgb(${r}, ${g}, ${b})`;
    }
}

/**
 * Get a human-readable risk label.
 */
export function getRiskLabel(score: number): 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' {
    if (score < 3) return 'LOW';
    if (score < 5) return 'MEDIUM';
    if (score < 8) return 'HIGH';
    return 'CRITICAL';
}

/**
 * Get an rgba CSS string for a glow/box-shadow effect based on risk score.
 */
export function getRiskGlow(score: number): string {
    const color = getRiskColor(score);
    const rgbMatch = color.match(/\d+/g);
    if (!rgbMatch || rgbMatch.length < 3) return 'rgba(0, 245, 255, 0.3)';

    const [r, g, b] = rgbMatch;
    const intensity = Math.min(score / 10, 1);
    const alpha = 0.2 + intensity * 0.5;
    return `rgba(${r}, ${g}, ${b}, ${alpha.toFixed(2)})`;
}

/**
 * Get the edge color for a specific channel type.
 */
export function getChannelColor(channel: string): string {
    const colors: Record<string, string> = {
        mobile: '#00f5ff',
        wallet: '#aa00ff',
        atm: '#ff2d55',
        bank: '#00ff88',
    };
    return colors[channel.toLowerCase()] ?? '#5a5a7a';
}
