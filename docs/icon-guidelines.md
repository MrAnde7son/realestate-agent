# Icon Usage Guidelines

The realestate-broker UI standardizes on [Lucide](https://lucide.dev/) for all iconography. This document captures the conventions for using icons across the application and documents the migration path away from Tabler icons.

## Why Lucide?
- **Consistency**: A single icon library ensures a cohesive look and feel.
- **Bundle size**: Importing from one package avoids duplicated glyphs.
- **API ergonomics**: Lucide provides tree-shakeable React components with a consistent naming scheme.

## General Usage Rules
1. **Only import from `lucide-react`**. Example:
   ```tsx
   import { Bell } from 'lucide-react';
   ```
2. **Prefer shared helpers** for repeated icon styling (e.g., size or color) instead of duplicating inline props.
3. **Avoid default exports**. Always import named icons to keep the bundle tree-shakeable.
4. **Add new icons here** when they are introduced so other developers can discover them quickly.

## Tabler → Lucide Mapping
Use the following mapping when replacing components that previously consumed Tabler icons.

| Tabler Icon (`@tabler/icons-react`) | Lucide Replacement (`lucide-react`) |
| ---------------------------------- | ------------------------------------ |
| `IconAlertCircle`                  | `AlertCircle`                        |
| `IconAlertTriangle`                | `AlertTriangle`                      |
| `IconBell`                         | `Bell`                               |
| `IconBookmark`                     | `Bookmark`                           |
| `IconBuilding`                     | `Building`                           |
| `IconCalendar`                     | `Calendar`                           |
| `IconCheck`                        | `Check`                              |
| `IconCheckCircle`                  | `CheckCircle`                        |
| `IconCopy`                         | `Copy`                               |
| `IconDownload`                     | `Download`                           |
| `IconExternalLink`                 | `ExternalLink`                       |
| `IconEye`                          | `Eye`                                |
| `IconEyeOff`                       | `EyeOff`                             |
| `IconFileText`                     | `FileText`                           |
| `IconFilter`                       | `Filter`                             |
| `IconKey`                          | `Key`                                |
| `IconLineChart`                    | `LineChart`                          |
| `IconMail`                         | `Mail`                               |
| `IconMapPin`                       | `MapPin`                             |
| `IconMenu2`                        | `Menu`                               |
| `IconPhone`                        | `Phone`                              |
| `IconRefresh`                      | `RefreshCw`                          |
| `IconSearch`                       | `Search`                             |
| `IconShield`                       | `Shield`                             |
| `IconStar`                         | `Star`                               |
| `IconStarOff`                      | `StarOff`                            |
| `IconTrash`                        | `Trash2`                             |
| `IconUsers`                        | `Users`                              |
| `IconZoomIn`                       | `ZoomIn`                             |

> ℹ️ **Tip:** Lucide icon names typically drop the `Icon` prefix and sometimes adjust the suffix (`RefreshCw`, `Trash2`). Use the [Lucide icon search](https://lucide.dev/icons) to confirm exact names when unsure.

## Adding New Icons
When a design requires an icon that is not listed above:
1. Search the Lucide gallery for the closest match.
2. Add the icon to this table with a short description of its usage context.
3. Update affected components to import from `lucide-react`.
4. Verify visual parity in Storybook or during manual QA.

## Legacy Components
If you encounter a component that still references `@tabler/icons-react`:
- Replace the import using the mapping above.
- Remove `@tabler/icons-react` from the component's dependencies.
- Mention the migration in the component's changelog or PR description.

Following these guidelines keeps the iconography consistent and avoids accidental reintroduction of Tabler icons.

> **Automated enforcement**: The UI test suite includes a guard that fails if any `@tabler/icons-react` imports resurface in the codebase. Run `pnpm test` inside `realestate-broker-ui/` to verify compliance before opening a PR.
