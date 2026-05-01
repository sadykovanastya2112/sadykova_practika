/**
 * Склонение существительных после числительных.
 */
export function pluralize(value) {
  const absValue = Math.abs(value) % 100
  const lastDigit = absValue % 10

  if (absValue > 10 && absValue < 20) return 'лет'
  if (lastDigit > 1 && lastDigit < 5) return 'года'
  if (lastDigit === 1) return 'год'
  return 'лет'
}
