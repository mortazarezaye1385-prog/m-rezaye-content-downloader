import type { QualityOption } from "../types/api";

/** The user must choose explicitly: nothing is pre-selected. */
export function findQuality(options: readonly QualityOption[] | null | undefined, id: string | null): QualityOption | null {
  if (!options || !id) return null;
  return options.find((o) => o.id === id) ?? null;
}

export function canDownloadQuality(options: readonly QualityOption[] | null | undefined, id: string | null): boolean {
  return findQuality(options, id) !== null;
}

/** Keep a selection only if it still exists after a refresh of the list. */
export function reconcileSelection(options: readonly QualityOption[] | null | undefined, id: string | null): string | null {
  return findQuality(options, id)?.id ?? null;
}
