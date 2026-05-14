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

function escapeHtml(text: string): string {
	const div = document.createElement('div')
	div.textContent = text
	return div.innerHTML
}

/**
 * Wraps each line of content in a div with line number and content spans.
 * Used for code preview rendering with line numbers.
 */
export function addLineNumbers(xml: string): string {
	const lines = xml.split('\n')
	const maxLineNum = lines.length
	const lineNumWidth = maxLineNum.toString().length

	return lines
		.map((line, index) => {
			const lineNum = (index + 1).toString().padStart(lineNumWidth, ' ')
			return `<div class="code-line"><span class="code-line-number">${lineNum}</span><span class="code-line-content">${escapeHtml(line || ' ')}</span></div>`
		})
		.join('')
}
