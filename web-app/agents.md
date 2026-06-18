# Porquilo — Web App

Vite + React 19 + TypeScript frontend. Talks to the FastAPI backend at `server/`.
Household-scale multi-user; bearer token auth required on all protected routes.

---

## Non-negotiables

- **No className-based styling** — all styles are inline `style` objects using CSS custom
  properties. Never add Tailwind, CSS Modules, or styled-components.
- **No routing library** — navigation is tab state managed in `App.tsx`. Do not install
  React Router or TanStack Router unless explicitly instructed.
- **TanStack Query for all server state** — never use `useEffect` + `fetch` directly in
  components. All API calls go through query/mutation hooks defined in `src/hooks/`.
- **TypeScript strict mode** — no `any`, no type assertions unless unavoidable, no `// @ts-ignore`.
- **Sentence case throughout the UI** — no ALL CAPS labels, no Title Case headings.
  Exception: 3-letter day abbreviations in the week strip (MON, TUE, etc.).

---

## Stack

| Concern      | Choice                                      |
|--------------|---------------------------------------------|
| Bundler      | Vite                                        |
| UI           | React 19                                    |
| Language     | TypeScript (strict)                         |
| Server state | TanStack Query v5 (`@tanstack/react-query`) |
| Testing      | Vitest + React Testing Library              |

---

## Project structure

```
porquilo-web/web-app/
  src/
    api/              ← Raw fetch functions, one file per resource
      client.ts       ← Base fetch wrapper (base URL, auth header, error handling)
      auth.ts         ← login, logout, changePassword, exchangePairingCode
      users.ts        ← admin: listUsers, createUser, deactivateUser, resetPassword, generatePairingCode
      diary.ts
      foods.ts
      entries.ts
      meals.ts
    components/       ← Shared primitives only (no view-specific logic)
      Icon.tsx              ← Icon component + WI icon map
      Button.tsx
      ConfidenceBadge.tsx
      MacroBar.tsx          ← takes raw numbers (kcal, protein, carbs, fat), not NutrientMap
      LogoMark.tsx
      MealSection.tsx
      RepeatMealRow.tsx
      SkippedMealRow.tsx
      ScaleStatusIndicator.tsx
      TableHeaders.tsx      ← shared table header row (Library, future tables)
      Num.tsx               ← monospace number cell with optional suffix
      TimeRangeSelector.tsx ← 7d/30d/90d/Custom pill group (Reports)
    views/            ← One folder per top-level tab
      today/
        TodayView.tsx
        WeekStrip.tsx
        SummaryCard.tsx
        DiaryCard.tsx
      library/
      reports/
      settings/
        SettingsView.tsx
        AccountSection.tsx        ← self-service password change + logout (all users);
                                     admin-only link to user management (web only)
        UserManagementSection.tsx ← admin only: create, deactivate/reactivate, reset
                                     password, generate per-user pairing QR (web only)
        ProfileSection.tsx
    hooks/            ← TanStack Query hooks, one file per resource
      useAuth.ts      ← current user query, login mutation, logout mutation
      useUsers.ts     ← admin user management queries/mutations
      useDiary.ts
      useFoods.ts
      useEntries.ts
      useMeals.ts
    types/
      api.ts          ← TypeScript types matching API response shapes exactly
    App.tsx           ← Root component, tab state
    main.tsx          ← Vite entry point
  index.html
  vite.config.ts
  tsconfig.json
```

---

## Styling

Tokens are defined in `../../Porquilo Design System/colors_and_type.css`. Read that file
before writing any new component — it is the source of truth for colors, typography,
spacing, radii, shadows, and motion values. Brand voice and tone are in
`../../Porquilo Design System/brand-brief.md`.

Rules:
- Use `var(--token)` always — never hard-code hex values or pixel values that duplicate a token.
- Tabular numbers on all numeric displays: `fontVariantNumeric: 'tabular-nums'`.
- `--font-mono` on: kcal figures, gram amounts, timestamps, version strings.
- `--font-display` (Newsreader) on: screen headings, meal section labels, panel titles.
  Always pair with `fontStyle: 'italic'` and `fontVariationSettings: "'opsz' 28"` (adjust
  optical size to match the rendered font size).

---

## API client

`src/api/client.ts` exports a base `apiFetch` function that:
- Prepends `import.meta.env.VITE_API_BASE_URL` (default `http://localhost:8000`)
- Sets `Content-Type: application/json` on POST/PUT
- Reads the bearer token from module-level state (set at login, cleared at logout) and
  attaches `Authorization: Bearer <token>` on every request
- On non-2xx, decodes the standard server error envelope
  `{"error": {"code": "...", "message": "...", "details": {...}}}` and throws an
  `ApiError` with `code`, `message`, and `details` fields — never throw on raw
  `.statusText` or assume a plain string body
- On 401, clears the stored token and triggers a re-login prompt

The bearer token is held in module-level state in `client.ts`, not React context or
props. `apiFetch` reads it directly. **Web token storage** (e.g. `localStorage`) is
not yet decided — treat this as an open decision when implementing the login flow.

Resource files import `apiFetch` and export typed async functions. They do not instantiate
TanStack Query — that happens in hooks.

---

## TanStack Query hooks

All hooks live in `src/hooks/`. Each hook wraps one API function.

```ts
// src/hooks/useDiary.ts — example shape
export function useDiary(date: string) {
  return useQuery({
    queryKey: ['diary', date],
    queryFn: () => getDiary(date),
  });
}
```

Mutation hooks use `useMutation` with `onSuccess` invalidating the relevant query key.
The `QueryClient` is created once in `main.tsx` — do not create additional instances.

---

## TypeScript types

All API response shapes live in `src/types/api.ts` and must match the Pydantic response
models in `server/` exactly. Define these before implementing any view:

```ts
type Confidence = 'measured' | 'estimated';  // two states only as of IA v0.4 — no 'calculated'
type NutrientMap = Record<string, number>;   // keyed by NutrientDefinition.key

interface DiaryEntry { ... }
interface DiaryMeal  { ... }  // entries[], meal totals, is_skipped
interface DiaryDay   { ... }  // meals[], day totals, has_estimated_entries

interface FoodResult { ... }  // id, name, brand, source, default_unit, nutrients, variants
interface Meal       { id: string; name: string; sort_order: number; }

// Auth & users
interface User {
  id: string;
  username: string;
  display_name: string;
  role: 'admin' | 'member';
  units: string;
  timezone: string;
}

interface AuthToken { token: string; user: User; }

interface ApiError { code: string; message: string; details: Record<string, unknown>; }
```

UUIDs from the API are typed as `string`. Do not import the `uuid` package.

---

## Component conventions

- Functional components only.
- Props interfaces named `{ComponentName}Props`, defined directly above the component.
- `components/` uses named exports. `views/` uses default exports.
- Shared primitives in `components/` must not import from `hooks/` or `api/` — data
  comes in as props.
- The canonical visual reference for all primitives is
  `../../Porquilo Design System/ui_kits/web/web-components.jsx`. When in doubt about
  a primitive's appearance or behaviour, read that file — do not guess.

---

## Testing

- Vitest with `jsdom` environment.
- React Testing Library for components — test behaviour, not implementation.
- Mock `fetch` with `vi.fn()` in API function tests. No real network calls.
- Hook tests: `renderHook` with a `QueryClientProvider` wrapper (`retry: false`,
  fresh `QueryClient` per test).
- No snapshot tests.