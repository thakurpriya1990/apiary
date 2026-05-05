# Bootstrap 3 to Bootstrap 5 Migration Plan

## Background

The majority of current bug tickets (styling issues, Toggle broken, popup dark background,
Missing Button Styling, etc.) share a root cause: Bootstrap 3 classes and attributes that
were removed or renamed in Bootstrap 5. This plan applies the full upgrade systematically
rather than fixing tickets one by one.

**In scope:**
- All `.vue` files under `disturbance/frontend/disturbance/src/` (81 files)
- All `.html` files under `disturbance/templates/disturbance/`

**Out of scope:**
- `base_original.html` (unused legacy file)
- `staticfiles_ds/` (build output — overwritten after Step 16)

## Workflow

After each step is implemented, the developer reviews the changes and commits manually before
proceeding to the next step. Do not move to the next step until the current one is committed.

---

## Progress

### Phase 1: Automated Find & Replace
- [x] Step 1: `pull-right` / `pull-left` -> `float-end` / `float-start`
- [x] Step 2: `btn-default` -> `btn-secondary`
- [ ] Step 3: `data-toggle` -> `data-bs-toggle`
- [ ] Step 4: `data-dismiss` -> `data-bs-dismiss`
- [ ] Step 5: `data-placement` -> `data-bs-placement`
- [ ] Step 6: `data-target` -> `data-bs-target`
- [ ] Step 7: Spacing utilities LTR -> logical properties
- [ ] Step 8: `col-sm-offset-N` -> `offset-sm-N`
- [ ] Step 9: `form-group` -> `mb-3`
- [ ] Step 10: `control-label` -> `col-form-label` / `form-label`
- [ ] Step 11: `collapse in` -> `collapse show`

### Phase 2: Structural HTML Changes
- [ ] Step 12: Fix alert dismiss button in `base.html`
- [ ] Step 13: Panel -> Card class conversion
- [ ] Step 14: Glyphicon -> Font Awesome icon conversion

### Phase 3: Build and Verification
- [ ] Step 15: Frontend build (`npm run build`)
- [ ] Step 16: Django collectstatic
- [ ] Step 17: Manual UI verification checklist

---

## Phase 1: Automated Find & Replace (sed scripts)

Low false-positive risk; safe to apply as mechanical string replacements.
Steps 1-11 can be run sequentially in a single shell session.

### Step 1: `pull-right` / `pull-left` -> `float-end` / `float-start` (~145 occurrences)

```bash
find /data/data/projects/apiary/disturbance/frontend/disturbance/src -name "*.vue" \
  -exec sed -i 's/\bpull-right\b/float-end/g; s/\bpull-left\b/float-start/g' {} +

find /data/data/projects/apiary/disturbance/templates/disturbance -name "*.html" \
  ! -name "base_original.html" \
  -exec sed -i 's/\bpull-right\b/float-end/g; s/\bpull-left\b/float-start/g' {} +
```

### Step 2: `btn-default` -> `btn-secondary` (~22 occurrences)

Rationale: `btn-default` removed in BS5. All Cancel/Processing buttons map to `btn-secondary`.

```bash
find /data/data/projects/apiary/disturbance/frontend/disturbance/src -name "*.vue" \
  -exec sed -i 's/\bbtn-default\b/btn-secondary/g' {} +
```

### Step 3: `data-toggle` -> `data-bs-toggle` (~35 occurrences + jQuery selectors)

Note: also updates jQuery selector strings like `'a[data-toggle="collapse"]'`.

```bash
find /data/data/projects/apiary/disturbance/frontend/disturbance/src -name "*.vue" \
  -exec sed -i 's/data-toggle=/data-bs-toggle=/g; s/\[data-toggle=/[data-bs-toggle=/g' {} +

find /data/data/projects/apiary/disturbance/templates/disturbance -name "*.html" \
  ! -name "base_original.html" \
  -exec sed -i 's/data-toggle=/data-bs-toggle=/g' {} +
```

### Step 4: `data-dismiss` -> `data-bs-dismiss` (2 occurrences)

```bash
sed -i 's/data-dismiss=/data-bs-dismiss=/g' \
  /data/data/projects/apiary/disturbance/templates/disturbance/base.html
```

### Step 5: `data-placement` -> `data-bs-placement` (6 occurrences)

Includes occurrences inside JS template literal strings.

```bash
find /data/data/projects/apiary/disturbance/frontend/disturbance/src -name "*.vue" \
  -exec sed -i 's/data-placement=/data-bs-placement=/g' {} +
```

### Step 6: `data-target` -> `data-bs-target` (1 occurrence)

```bash
find /data/data/projects/apiary/disturbance/templates/disturbance -name "*.html" \
  ! -name "base_original.html" \
  -exec sed -i 's/data-target=/data-bs-target=/g' {} +
```

### Step 7: Spacing utilities LTR -> logical properties (7 occurrences)

`ml-N` -> `ms-N`, `mr-N` -> `me-N`, `pl-N` -> `ps-N`, `pr-N` -> `pe-N`

```bash
find /data/data/projects/apiary/disturbance/frontend/disturbance/src -name "*.vue" \
  -exec sed -i \
    's/\bml-\([0-9]\)/ms-\1/g; s/\bmr-\([0-9]\)/me-\1/g;
     s/\bpl-\([0-9]\)/ps-\1/g; s/\bpr-\([0-9]\)/pe-\1/g' {} +
```

### Step 8: `col-sm-offset-N` -> `offset-sm-N` (2 occurrences, primarily `submit.vue`)

```bash
find /data/data/projects/apiary/disturbance/frontend/disturbance/src -name "*.vue" \
  -exec sed -i 's/col-\([a-z]*\)-offset-\([0-9]*\)/offset-\1-\2/g' {} +
```

### Step 9: `form-group` -> `mb-3` (~114 occurrences)

Handle `form-group row` / `row form-group` in a first pass to avoid double-processing.

```bash
find /data/data/projects/apiary/disturbance/frontend/disturbance/src -name "*.vue" \
  -exec sed -i \
    's/form-group row/row mb-3/g; s/row form-group/row mb-3/g; s/\bform-group\b/mb-3/g' {} +

find /data/data/projects/apiary/disturbance/templates/disturbance -name "*.html" \
  ! -name "base_original.html" \
  -exec sed -i \
    's/form-group row/row mb-3/g; s/row form-group/row mb-3/g; s/\bform-group\b/mb-3/g' {} +
```

### Step 10: `control-label` -> `col-form-label` / `form-label` (~113 occurrences)

Two passes: when paired with a `col-*` class use `col-form-label`; remaining standalone
instances use `form-label`.

```bash
# Pass 1: alongside col-* -> col-form-label
find /data/data/projects/apiary/disturbance/frontend/disturbance/src -name "*.vue" \
  -exec sed -i 's/\(col-[a-z0-9-]* \)control-label/\1col-form-label/g' {} +
find /data/data/projects/apiary/disturbance/templates/disturbance -name "*.html" \
  ! -name "base_original.html" \
  -exec sed -i 's/\(col-[a-z0-9-]* \)control-label/\1col-form-label/g' {} +

# Pass 2: remaining standalone -> form-label
find /data/data/projects/apiary/disturbance/frontend/disturbance/src -name "*.vue" \
  -exec sed -i 's/\bcontrol-label\b/form-label/g' {} +
find /data/data/projects/apiary/disturbance/templates/disturbance -name "*.html" \
  ! -name "base_original.html" \
  -exec sed -i 's/\bcontrol-label\b/form-label/g' {} +
```

### Step 11: `collapse in` -> `collapse show` (initial open state)

The `in` active class was renamed to `show` in BS5.

```bash
find /data/data/projects/apiary/disturbance/frontend/disturbance/src -name "*.vue" \
  -exec sed -i 's/collapse in\b/collapse show/g' {} +

find /data/data/projects/apiary/disturbance/templates/disturbance -name "*.html" \
  ! -name "base_original.html" \
  -exec sed -i 's/collapse in\b/collapse show/g' {} +
```

---

## Phase 2: Structural HTML Changes

Depends on: Phase 1 complete.
More complex — requires tag-level edits rather than simple token replacement.

### Step 12: Fix alert dismiss button in `base.html`

File: `disturbance/templates/disturbance/base.html`

Before:
```html
<button type="button" class="close" data-dismiss="alert" aria-hidden="true">&#215;</button>
```
After:
```html
<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
```
Note: `data-bs-dismiss` is already set by Step 4; only `class` and inner content need updating here.

### Step 13: Panel -> Card class conversion

Target files:
- `disturbance/frontend/disturbance/src/components/user/manage_organisation.vue`
- `disturbance/frontend/disturbance/src/components/external/organisations/manage.vue`
- `disturbance/frontend/disturbance/src/components/external/proposal_apply.vue`
- `disturbance/frontend/disturbance/src/components/external/proposal_apply_new.vue`
- `disturbance/frontend/disturbance/src/components/forms/section_toggle_orig.vue`
- `disturbance/frontend/disturbance/src/components/internal/referrals/apiary_referral.vue`
- `disturbance/frontend/disturbance/src/components/internal/proposals/apiary_proposal_requirements.vue`
- `disturbance/templates/disturbance/user_profile.html`

Replacement rules:
- `panel panel-default` -> `card`
- `panel panel-primary` -> `card border-primary`
- `panel-heading` -> `card-header`
- `panel-body` -> `card-body`
- `panel-footer` -> `card-footer`
- `panel-title` -> `card-title`
- `panel-group` -> `accordion`

```bash
for file in \
  "/data/data/projects/apiary/disturbance/frontend/disturbance/src/components/user/manage_organisation.vue" \
  "/data/data/projects/apiary/disturbance/frontend/disturbance/src/components/external/organisations/manage.vue" \
  "/data/data/projects/apiary/disturbance/frontend/disturbance/src/components/external/proposal_apply.vue" \
  "/data/data/projects/apiary/disturbance/frontend/disturbance/src/components/external/proposal_apply_new.vue" \
  "/data/data/projects/apiary/disturbance/frontend/disturbance/src/components/forms/section_toggle_orig.vue" \
  "/data/data/projects/apiary/disturbance/frontend/disturbance/src/components/internal/referrals/apiary_referral.vue" \
  "/data/data/projects/apiary/disturbance/frontend/disturbance/src/components/internal/proposals/apiary_proposal_requirements.vue" \
  "/data/data/projects/apiary/disturbance/templates/disturbance/user_profile.html"; do
  sed -i \
    's/panel panel-default/card/g;
     s/panel panel-primary/card border-primary/g;
     s/\bpanel-heading\b/card-header/g;
     s/\bpanel-body\b/card-body/g;
     s/\bpanel-footer\b/card-footer/g;
     s/\bpanel-title\b/card-title/g;
     s/\bpanel-group\b/accordion/g' "$file"
done
```

### Step 14: Glyphicon -> Font Awesome icon conversion

Target files:
- `disturbance/frontend/disturbance/src/components/user/manage_organisation.vue` (jQuery toggleClass x2)
- `disturbance/frontend/disturbance/src/components/external/organisations/manage.vue` (jQuery toggleClass x1)
- `disturbance/frontend/disturbance/src/components/external/proposal_apply.vue` (chevron-up in HTML)
- `disturbance/frontend/disturbance/src/components/external/proposal_apply_new.vue` (chevron-up in HTML)
- `disturbance/frontend/disturbance/src/components/form_apiary.vue` (calendar icon)
- `disturbance/templates/disturbance/user_profile.html` (chevron-up / chevron-down x4)

HTML class replacement:
```bash
find /data/data/projects/apiary/disturbance/frontend/disturbance/src -name "*.vue" \
  -exec sed -i \
    's/glyphicon glyphicon-chevron-up/fa fa-chevron-up/g;
     s/glyphicon glyphicon-chevron-down/fa fa-chevron-down/g;
     s/glyphicon glyphicon-calendar/fa fa-calendar/g;
     s/glyphicon glyphicon-/fa fa-/g' {} +

sed -i \
  's/glyphicon glyphicon-chevron-up/fa fa-chevron-up/g;
   s/glyphicon glyphicon-chevron-down/fa fa-chevron-down/g' \
  /data/data/projects/apiary/disturbance/templates/disturbance/user_profile.html
```

JavaScript toggleClass fix:
```bash
find /data/data/projects/apiary/disturbance/frontend/disturbance/src -name "*.vue" \
  -exec sed -i \
    "s/toggleClass('glyphicon-chevron-down glyphicon-chevron-up')/toggleClass('fa-chevron-down fa-chevron-up')/g;
     s/toggleClass(\"glyphicon-chevron-down glyphicon-chevron-up\")/toggleClass('fa-chevron-down fa-chevron-up')/g" {} +
```

---

## Phase 3: Build and Verification

Depends on: Phase 2 complete.

### Step 15: Frontend build

```bash
cd /data/data/projects/apiary/disturbance/frontend/disturbance
npm run build
```
Fix any build errors before proceeding.

### Step 16: Django collectstatic

```bash
cd /data/data/projects/apiary
python manage_ds.py collectstatic --noinput
```

### Step 17: Manual UI verification checklist

1. **Button styling** - Cancel and Processing buttons render correctly as `btn-secondary`
2. **Accordion / collapse** - Collapsible sections in `user_profile.html` and `manage_organisation.vue` open and close
3. **Popovers** - Popovers appear on hover/click in table rows
4. **Alert dismissal** - Django messages alerts close when the x button is clicked
5. **Modal backdrop** - Dialogs open/close correctly; background is translucent grey, not solid black
6. **Form label alignment** - Labels are correctly aligned (`col-form-label` vs `form-label`)
7. **Panel -> Card rendering** - proposal_apply and organisations pages render cards without layout breakage
8. **Chevron icons** - Chevron icons are visible and toggle up/down on click

---

## Files Modified Summary

### Phase 1 - bulk replacement targets
- All 81 `.vue` files under `disturbance/frontend/disturbance/src/components/`
- All `.html` files under `disturbance/templates/disturbance/` (excluding `base_original.html`)

### Phase 2 - targeted structural edits
- `disturbance/templates/disturbance/base.html` - Step 12
- `disturbance/frontend/disturbance/src/components/user/manage_organisation.vue` - Steps 13, 14
- `disturbance/frontend/disturbance/src/components/external/organisations/manage.vue` - Steps 13, 14
- `disturbance/frontend/disturbance/src/components/external/proposal_apply.vue` - Steps 13, 14
- `disturbance/frontend/disturbance/src/components/external/proposal_apply_new.vue` - Steps 13, 14
- `disturbance/frontend/disturbance/src/components/forms/section_toggle_orig.vue` - Step 13
- `disturbance/frontend/disturbance/src/components/internal/referrals/apiary_referral.vue` - Step 13
- `disturbance/frontend/disturbance/src/components/internal/proposals/apiary_proposal_requirements.vue` - Step 13
- `disturbance/frontend/disturbance/src/components/form_apiary.vue` - Step 14
- `disturbance/templates/disturbance/user_profile.html` - Steps 13, 14

---

## Decisions

- All `btn-default` -> `btn-secondary` (Cancel and Processing buttons alike)
- `control-label` with `col-*` -> `col-form-label`; standalone -> `form-label`
- Glyphicon replacement uses Font Awesome 4.7 (`fa fa-*` syntax already in use)
- `base_original.html` excluded (unused legacy file)
- `staticfiles_ds/` excluded (build output, overwritten by Step 16)
