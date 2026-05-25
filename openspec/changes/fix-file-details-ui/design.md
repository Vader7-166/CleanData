## Context

The file details view, implemented as a modal in the Frontend, suffers from several UI regressions:
1. Content overflow: Large amounts of processed data in the detail view extend beyond the screen boundaries without proper scrolling.
2. Invisibility: Text is rendered in white on a white background, making it unreadable.
3. Stuck state: The modal cannot be dismissed easily because the close button is either hidden by the overflow or non-functional.

## Goals / Non-Goals

**Goals:**
- Fix the CSS overflow to keep the modal within the viewport.
- Ensure all text in the modal is readable with proper contrast.
- Ensure the modal can be closed via a visible button and clicking outside/pressing ESC.

**Non-Goals:**
- Redesigning the data processing logic.
- Changing the data structure of the file details.

## Decisions

- **Decision 1: Use Tailwind Scrollbars and Constraints**: Apply `max-h-[90vh]` and `overflow-y-auto` to the modal content container to ensure it stays within the screen.
- **Decision 2: Explicit Text Coloring**: Instead of relying on inherited colors, explicitly set text colors (e.g., `text-slate-900`) for the modal content to prevent white-on-white issues.
- **Decision 3: Standardize Modal Controls**: Use the existing UI library's modal components (if available) or implement a fixed-position close button at the top-right of the modal.

## Risks / Trade-offs

- [Risk] → Fixed colors might not work well if a Dark Mode is implemented later.
- [Mitigation] → Use Tailwind's semantic color classes (e.g., `text-foreground`) that respond to theme changes, or ensure explicit light-theme colors for now.
