---
name: bohrium-app-info-brief
description: Create bilingual Bohrium App listing/info Markdown documents from a given scientific app name, repository, paper, tool, or app idea. Use when Codex is asked to prepare Bohrium App basics such as appKey, app name, Chinese/English descriptions, four independent Markdown-rendered content pages (Chinese intro, English intro, Chinese help, English help), cover image prompt or asset, per-page references, assumptions, and pending runtime/image contract items before building the actual Bohrium image or release.
---

# Bohrium App Info Brief

Draft a reusable App information document for Bohrium before implementation, image building, or release. Treat Chinese intro, English intro, Chinese help, and English help as four separate Markdown-rendered pages. Keep product copy, evidence, assumptions, and runtime TODOs separate.

## Workflow

1. Identify the target App from the user's app name, repo, paper, URL, existing files, or short idea.
2. Inspect local project files first. If the App depends on external papers, repos, APIs, Bohrium pages, or current platform behavior, browse or query primary sources and record links.
3. If the user provides a Bohrium reference App page, inspect it for field shape. Dynamic pages may require checking frontend bundles or API responses; state when evidence is inferred from UI code rather than page content.
4. Draft a Markdown document in the current project, usually under `docs/<app-key>-bohrium-app-info.md`.
5. Include every required listing field:
   - App identifier / `appKey`
   - App name
   - Chinese description
   - English description
   - Chinese App introduction Markdown page
   - English App introduction Markdown page
   - Chinese help document title and Markdown page
   - English help document title and Markdown page
   - Cover image path or generation prompt
6. Add references inside each of the four independent Markdown pages when claims depend on papers, repositories, model cards, benchmarks, or platform behavior. Use numbered references like `[1]`, `[2]` within that page and include a local `参考文献` or `References` subsection before that page ends. Do not put references only at the end of the combined planning document.
7. Add a `后续镜像与运行契约待补` section for unimplemented runtime facts. Do not present image names, SDK versions, resource SKUs, schemas, pricing, license status, or release checks as finished unless verified.
8. If a cover image is requested or useful for the App listing, use the image generation skill/tool. Save the final project-bound image in the workspace, commonly `assets/cover/<app-key>-cover.png`, and reference it from the Markdown.
9. Validate that relative image links resolve, the document is readable, and no secrets or unverified platform mutations are included.

## Document Shape

Use `references/app-info-template.md` as the base structure when creating a new document. Adapt headings only when the user's target platform field names require it.

## Copy Rules

- Keep short descriptions concise enough for a marketplace/listing card.
- Make introductions scientifically specific, but avoid claiming experimental validation or practical efficacy unless the source supports it.
- Make each of the four Markdown-rendered content pages self-contained. A user should be able to copy only one page into Bohrium and still keep its citations.
- State computational outputs as hypothesis-generating research results.
- Use bilingual content with matched meaning, not word-for-word translation when English needs clearer scientific phrasing.
- Prefer conservative `appKey` values: lowercase letters, digits, and hyphens. If uniqueness is uncertain, mark it as suggested.
- Keep implementation details pending until the actual image, adapter, inputs, outputs, and Bohrium release path are known.

## References

Use primary sources first:

- Official code repositories, docs, model cards, schemas, and executable help.
- Peer-reviewed papers or preprints for scientific claims.
- Bohrium documentation, UI, or read-only API evidence for platform fields.

Classify uncertain material directly in the document as `待确认`, `建议`, or `inference`. Never cite broad search snippets as the only evidence for a scientific or platform claim when a primary source is available. A final evidence section in the combined document is allowed for internal tracking, but it must not be the only place where citations appear for the four rendered pages.
