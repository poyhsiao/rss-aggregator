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