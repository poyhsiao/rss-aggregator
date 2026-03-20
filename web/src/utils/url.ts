interface ParsedUrl {
  display: string
  full: string
  domain: string
  path: string
}

export function formatUrl(url: string, maxLength: number = 40): ParsedUrl {
  try {
    const urlObj = new URL(url)
    const domain = urlObj.hostname
    const path = urlObj.pathname + urlObj.search

    let display: string

    if (url.length <= maxLength) {
      display = url
    } else {
      const pathLength = maxLength - domain.length - 3

      if (pathLength > 10) {
        display = `${domain}...${path.slice(-pathLength)}`
      } else {
        display = `${domain}${path.length > 0 ? '/...' : ''}`
      }
    }

    return {
      display,
      full: url,
      domain,
      path,
    }
  } catch {
    return {
      display: url.length > maxLength ? `${url.slice(0, maxLength)}...` : url,
      full: url,
      domain: url,
      path: '',
    }
  }
}

export function truncateUrl(url: string, mobileChars: number = 25, desktopChars: number = 50): { mobile: string; desktop: string; full: string } {
  return {
    mobile: url.length > mobileChars ? `${url.slice(0, mobileChars)}...` : url,
    desktop: url.length > desktopChars ? `${url.slice(0, desktopChars)}...` : url,
    full: url,
  }
}