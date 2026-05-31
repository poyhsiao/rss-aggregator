/**
 * Cleans content by removing surrounding quotes if present (from JSON stringification).
 * Preserves content that starts with `<` (e.g., XML).
 */
export function cleanContent(content: string): string {
	if (!content) return ''
	let cleaned = content.trim()
	if (
		(cleaned.startsWith('"') && cleaned.endsWith('"')) ||
		(cleaned.startsWith("'") && cleaned.endsWith("'"))
	) {
		if (!cleaned.slice(1, -1).trim().startsWith('<')) {
			cleaned = cleaned.slice(1, -1)
		}
	}
	return cleaned
}

export function addLineNumbers(html: string): string {
	const lines = html.split('\n')
	const maxLineNum = lines.length
	const lineNumWidth = maxLineNum.toString().length

	return lines
		.map((line, index) => {
			const lineNum = (index + 1).toString().padStart(lineNumWidth, ' ')
			const escapedLineNum = lineNum.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
			return `<span class="code-line"><span class="code-line-number">${escapedLineNum}</span><span class="code-line-content">${line || ' '}</span></span>`
		})
		.join('')
}
