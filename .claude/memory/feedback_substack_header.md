---
name: Substack post header — title + subtitle
description: Every Daybreak Substack post must open with an h1 title and a fixed subtitle line
type: feedback
originSessionId: ae1ac99b-002d-491d-9fd1-df3e1f43f90c
---
After the user approves the final title, add it to the top of the Substack HTML as:

```html
<h1>[APPROVED TITLE]</h1>
<p><em>The Morning Brief · Market intelligence at the open</em></p>
```

The subtitle is fixed and never changes. The title is the one the user picks from the 5 options.

**Why:** User confirmed this format on 2026-05-08.

**How to apply:** In Step 3 of the daybreak skill, the Substack HTML must always open with these two elements. Write the post body first, then prepend title + subtitle once the user has picked the title.
