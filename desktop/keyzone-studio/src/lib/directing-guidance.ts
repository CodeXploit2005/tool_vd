export function directingGuidance(aspectRatio: string) {
  return `# Optional directing guidance
Follow the creator's requested style, camera, pace and ending. Use these suggestions only where the brief leaves a choice:
Give each shot a visible action or change. Pick framing that reveals it clearly. Across cuts, keep screen direction, props and character identity legible. If the creator wants a single take, plan successive moments of one continuous action rather than forcing angle changes.
${aspectRatio === "9:16" ? "For vertical framing, keep essential action readable on a phone and clear of interface edges. Use the opening beat that suits this story; a quiet opening is valid." : "Use the width to show relationships between subjects when useful."}`;
}
