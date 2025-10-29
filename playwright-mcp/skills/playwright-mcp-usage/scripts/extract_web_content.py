#!/usr/bin/env python3
"""
Site-agnostic web content extractor using Playwright.

This script is intentionally generic - the calling agent specifies:
- Which CSS selectors to try
- How long to wait
- Whether to handle cookie popups

Usage:
    python extract_web_content.py <url> <output_file> \\
        --selectors "main" "article" "[role=main]" \\
        --wait-time 5000 \\
        --cookie-button "Accept cookies"
"""

from playwright.sync_api import sync_playwright
import sys
import argparse
import json
from pathlib import Path


def extract_content(url: str, output_file: str,
                   selectors: list[str],
                   wait_time: int = 3000,
                   cookie_button: str = None,
                   use_profile: bool = False,
                   cdp_url: str = None) -> dict:
    """
    Extract web content and save to file.

    Args:
        url: Web page URL
        output_file: Path to output file
        selectors: List of CSS selectors to try (in order)
        wait_time: Wait time in milliseconds before extraction
        cookie_button: Optional button text for cookie acceptance
        use_profile: Use logged-in Edge profile for authentication (launches new instance)
        cdp_url: Connect to running Edge via CDP (e.g., http://localhost:9222)

    Returns:
        dict with success status and metadata
    """

    try:
        with sync_playwright() as p:
            if cdp_url:
                # Connect to running Edge instance via CDP
                print(f"[0/4] Connecting to running Edge at: {cdp_url}", file=sys.stderr)
                browser = p.chromium.connect_over_cdp(cdp_url)
                # Get the default context (the existing browser session)
                contexts = browser.contexts
                if contexts:
                    context = contexts[0]
                else:
                    context = browser.new_context()
                page = context.new_page()
            elif use_profile:
                # Use persistent context with user's Edge profile
                from pathlib import Path as PathLib
                profile_path = str(PathLib.home() / "Library/Application Support/Microsoft Edge/Default")
                print(f"[0/4] Using Edge profile: {profile_path}", file=sys.stderr)
                print(f"      Note: Close all Edge windows first to avoid profile lock issues", file=sys.stderr)

                context = p.chromium.launch_persistent_context(
                    profile_path,
                    channel="msedge",
                    headless=False
                )
                page = context.new_page()
            else:
                # Launch browser (visible mode) without profile
                browser = p.chromium.launch(
                    channel="msedge",
                    headless=False
                )

                context = browser.new_context()
                page = context.new_page()

            # Navigate
            print(f"[1/4] Navigating to {url}...", file=sys.stderr)
            page.goto(url, wait_until="domcontentloaded")

            # Handle cookie popup if specified
            if cookie_button:
                print(f"[2/4] Looking for cookie button: '{cookie_button}'...", file=sys.stderr)
                try:
                    page.wait_for_selector(f"button:has-text('{cookie_button}')", timeout=2000)
                    page.click(f"button:has-text('{cookie_button}')")
                    print(f"      ✓ Clicked cookie button", file=sys.stderr)
                except:
                    print(f"      - No cookie button found (or already accepted)", file=sys.stderr)
            else:
                print(f"[2/4] Skipping cookie handling", file=sys.stderr)

            # Wait for content
            print(f"[3/4] Waiting {wait_time}ms for content to load...", file=sys.stderr)
            page.wait_for_timeout(wait_time)

            # Extract content - try selectors in order
            print(f"[4/4] Extracting content...", file=sys.stderr)
            print(f"      Trying selectors: {selectors}", file=sys.stderr)

            result = page.evaluate("""
                (selectors) => {
                    // Try each selector until we find content
                    for (const selector of selectors) {
                        try {
                            const element = document.querySelector(selector);
                            if (element && element.innerText && element.innerText.trim().length > 100) {
                                return {
                                    success: true,
                                    content: element.innerText,
                                    selector: selector,
                                    charCount: element.innerText.length,
                                    lineCount: element.innerText.split('\\n').length,
                                    title: document.title
                                };
                            }
                        } catch (e) {
                            // Selector failed, try next
                        }
                    }

                    // No selector worked
                    return {
                        success: false,
                        error: 'No selector returned content > 100 chars',
                        attempted: selectors
                    };
                }
            """, selectors)

            context.close()

            if not result['success']:
                return {
                    'success': False,
                    'error': result.get('error', 'Content extraction failed'),
                    'attempted_selectors': result.get('attempted', [])
                }

            # Write to file
            print(f"      ✓ Extracted using selector: {result['selector']}", file=sys.stderr)
            print(f"      Writing to {output_file}...", file=sys.stderr)

            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(result['content'])

            # Return metadata
            return {
                'success': True,
                'output_file': str(output_path.absolute()),
                'char_count': result['charCount'],
                'line_count': result['lineCount'],
                'title': result['title'],
                'selector_used': result['selector']
            }

    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def main():
    parser = argparse.ArgumentParser(
        description='Site-agnostic web content extractor. The calling agent specifies the extraction strategy.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Notion page (agent specifies selectors)
  python extract_web_content.py "https://notion.so/page" output.md \\
      --selectors "main" "[role=main]" \\
      --wait-time 7000

  # Substack article (agent specifies selectors and cookie handling)
  python extract_web_content.py "https://example.substack.com/p/post" output.md \\
      --selectors ".available-content" ".post-content" "article" \\
      --wait-time 3000 \\
      --cookie-button "Accept"

  # Generic site (agent provides best guess)
  python extract_web_content.py "https://example.com/article" output.md \\
      --selectors "article" "main" ".content" "#content"
        """
    )

    parser.add_argument('url', help='Web page URL')
    parser.add_argument('output_file', help='Output file path')
    parser.add_argument('--selectors', nargs='+', required=True,
                       metavar='SELECTOR',
                       help='CSS selectors to try (in order, stops at first match)')
    parser.add_argument('--wait-time', type=int, default=3000,
                       metavar='MS',
                       help='Wait time in milliseconds (default: 3000)')
    parser.add_argument('--cookie-button', metavar='TEXT',
                       help='Cookie acceptance button text (e.g., "Accept", "Accept cookies")')
    parser.add_argument('--use-profile', action='store_true',
                       help='Use logged-in Edge profile (launches new instance, close Edge first)')
    parser.add_argument('--cdp-url', metavar='URL',
                       help='Connect to running Edge via CDP (e.g., http://localhost:9222)')

    args = parser.parse_args()

    result = extract_content(
        args.url,
        args.output_file,
        selectors=args.selectors,
        wait_time=args.wait_time,
        cookie_button=args.cookie_button,
        use_profile=args.use_profile,
        cdp_url=args.cdp_url
    )

    if result['success']:
        print(f"\n✓ Success!", file=sys.stderr)
        print(f"  File: {result['output_file']}", file=sys.stderr)
        print(f"  Size: {result['char_count']:,} characters", file=sys.stderr)
        print(f"  Lines: {result['line_count']:,}", file=sys.stderr)
        print(f"  Title: {result['title']}", file=sys.stderr)
        print(f"  Selector: {result['selector_used']}", file=sys.stderr)

        # Output JSON for programmatic use
        print(json.dumps(result))
        sys.exit(0)
    else:
        print(f"\n✗ Failed: {result['error']}", file=sys.stderr)
        if 'attempted_selectors' in result:
            print(f"  Attempted selectors: {result['attempted_selectors']}", file=sys.stderr)
            print(f"\n  Hint: The agent should try different selectors or increase wait time", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
