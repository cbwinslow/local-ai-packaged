import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

/**
 * Composes class names and merges/deduplicates Tailwind CSS utility classes.
 *
 * @param inputs - One or more class values (strings, arrays, or objects) to compose.
 * @returns The resulting className string with conflicting Tailwind classes resolved.
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}