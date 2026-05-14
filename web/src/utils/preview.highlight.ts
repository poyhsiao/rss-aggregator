import hljs from 'highlight.js'

export function highlightJson(json: string): string {
  try {
    return hljs.highlight(json, { language: 'json' }).value
  } catch {
    return manualHighlightJson(json)
  }
}

export function manualHighlightJson(json: string): string {
  json = json
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')

  let result = ''
  let i = 0

  while (i < json.length) {
    if (json[i] === '"') {
      let stringStart = i
      i++
      while (i < json.length) {
        if (json[i] === '\\' && i + 1 < json.length) {
          i += 2
        } else if (json[i] === '"') {
          i++
          break
        } else {
          i++
        }
      }
      const stringContent = json.substring(stringStart, i)

      let j = i
      while (j < json.length && /\s/.test(json[j])) j++
      const isKey = json[j] === ':'

      if (isKey) {
        result += `<span class="json-key">${stringContent}</span>`
      } else {
        result += `<span class="json-string">${stringContent}</span>`
      }
    }
    else if (json[i] === '-' || (json[i] >= '0' && json[i] <= '9')) {
      let numStart = i
      if (json[i] === '-') i++
      while (i < json.length && /[\d.eE+-]/.test(json[i])) i++
      result += `<span class="json-number">${json.substring(numStart, i)}</span>`
    }
    else if (json.substring(i, i + 4) === 'true') {
      result += '<span class="json-boolean">true</span>'
      i += 4
    }
    else if (json.substring(i, i + 5) === 'false') {
      result += '<span class="json-boolean">false</span>'
      i += 5
    }
    else if (json.substring(i, i + 4) === 'null') {
      result += '<span class="json-null">null</span>'
      i += 4
    }
    else {
      result += json[i]
      i++
    }
  }

  return result
}

export function highlightXml(xml: string): string {
	xml = xml
		.replace(/&/g, '&amp;')
		.replace(/</g, '&lt;')
		.replace(/>/g, '&gt;')
		.replace(/"/g, '&quot;')

	// Highlight XML tags
	xml = xml.replace(/(&lt;\/?)([\w:.-]+)(&gt;)/g, (_match, open, tag, close) => {
		return `<span class="xml-tag-bracket">${open}</span><span class="xml-tag-name">${tag}</span><span class="xml-tag-bracket">${close}</span>`
	})

	// Highlight attributes
	xml = xml.replace(/(\s)([\w:.-]+)(=)(&quot;[^&]*&quot;)/g, (_match, space, attr, eq, value) => {
		return `${space}<span class="xml-attr-name">${attr}</span>${eq}<span class="xml-attr-value">${value}</span>`
	})

	// Highlight CDATA sections
	xml = xml.replace(/(&lt;\!\[CDATA\[)([\s\S]*?)(\]\]&gt;)/g, (_match, open, content, close) => {
		return `<span class="xml-cdata">${open}${content}${close}</span>`
	})

	// Highlight comments
	xml = xml.replace(/(&lt;!--)([\s\S]*?)(--&gt;)/g, (_match, open, content, close) => {
		return `<span class="xml-comment">${open}${content}${close}</span>`
	})

	// Highlight processing instructions
	xml = xml.replace(/(&lt;\?)([\w:.-]+)(.*?)(\?&gt;)/g, (_match, open, target, content, close) => {
		return `<span class="xml-pi">${open}${target}${content}${close}</span>`
	})

	return xml
}

export function escapeHtml(text: string): string {
	return text
		.replace(/&/g, '&amp;')
		.replace(/</g, '&lt;')
		.replace(/>/g, '&gt;')
}

export function highlightMarkdownSource(source: string): string {
	let result = escapeHtml(source)

	const codeBlocks: { placeholder: string; html: string }[] = []

	result = result.replace(/```(\w*)\n([\s\S]*?)```/g, (_match, lang, code) => {
		let highlightedCode: string
		if (lang && hljs.getLanguage(lang)) {
			try {
				highlightedCode = hljs.highlight(code.trim(), { language: lang }).value
			} catch {
				highlightedCode = hljs.highlightAuto(code.trim()).value
			}
		} else {
			highlightedCode = hljs.highlightAuto(code.trim()).value
		}
		const placeholder = `__CODE_BLOCK_${codeBlocks.length}__`
		codeBlocks.push({
			placeholder,
			html: `<div class="source-code-block"><code class="language-${lang || 'text'}">${highlightedCode}</code></div>`
		})
		return placeholder
	})

	result = result.replace(/`([^`\n]+)`/g, '<code class="source-inline-code">$1</code>')

	for (const block of codeBlocks) {
		result = result.replace(block.placeholder, block.html)
	}

	result = result.replace(/^(#{1,6})\s(.*)$/gm, '<span class="md-header">$1</span> <span class="md-header-text">$2</span>')
	result = result.replace(/\*\*([^*\n]+)\*\*/g, '<span class="md-bold">$1</span>')
	result = result.replace(/(?<!\*)\*([^*\n]+)\*(?!\*)/g, '<span class="md-italic">$1</span>')
	result = result.replace(/\[([^\]\n]+)\]\(([^)\n]+)\)/g, '<span class="md-link-text">$1</span> <span class="md-link-url">($2)</span>')
	result = result.replace(/^(\s*)([-*+])(\s)/gm, '$1<span class="md-list">$2</span>$3')
	result = result.replace(/^(---)$/gm, '<span class="md-hr">$1</span>')
	result = result.replace(/^(&gt;\s?.*)$/gm, '<span class="md-quote">$1</span>')

	return result
}