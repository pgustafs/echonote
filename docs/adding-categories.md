# Adding New Categories to EchoNote

This guide explains how to manually add a new transcription category to the EchoNote application.

## Overview

Categories allow users to organize their transcriptions by content type (e.g., Meeting Notes, LinkedIn Post, Email Draft, etc.). Adding a new category requires updates to both backend and frontend code.

## Prerequisites

- Access to the codebase
- Ability to rebuild Docker/Podman containers
- Basic understanding of Python enums and TypeScript types

## Steps to Add a New Category

### 1. Update Backend Category Enum

**File:** `/backend/models.py`

Add your new category to the `Category` enum class:

```python
class Category(str, Enum):
    """Categories for organizing transcriptions by content type"""
    VOICE_MEMO = "voice_memo"
    MEETING_NOTES = "meeting_notes"
    LINKEDIN_POST = "linkedin_post"
    EMAIL_DRAFT = "email_draft"
    BLOG_POST = "blog_post"
    TODO_LIST = "todo_list"
    TWEET = "tweet"
    YOUTUBE_DESCRIPTION = "youtube_description"
    PRODUCT_REQUIREMENTS = "product_requirements"
    CUSTOMER_FEEDBACK = "customer_feedback"
    BRAINSTORM = "brainstorm"
    INTERVIEW_NOTES = "interview_notes"
    JOURNAL_ENTRY = "journal_entry"
    NEWSLETTER = "newsletter"
    DOCUMENTATION = "documentation"
    # Add your new category here:
    MY_NEW_CATEGORY = "my_new_category"  # Use snake_case
```

**Important:**
- Use `UPPER_SNAKE_CASE` for the enum key
- Use `lower_snake_case` for the enum value
- The value will be stored in the database

### 2. Update Frontend TypeScript Type

**File:** `/frontend/src/types.ts`

Add your new category to the `Category` type:

```typescript
export type Category =
  | 'voice_memo'
  | 'meeting_notes'
  | 'linkedin_post'
  | 'email_draft'
  | 'blog_post'
  | 'todo_list'
  | 'tweet'
  | 'youtube_description'
  | 'product_requirements'
  | 'customer_feedback'
  | 'brainstorm'
  | 'interview_notes'
  | 'journal_entry'
  | 'newsletter'
  | 'documentation'
  | 'my_new_category'  // Add your new category here
```

### 3. Update Category Labels

**File:** `/frontend/src/utils/categoryUtils.ts`

Add labels for your new category in three places:

#### 3.1 Full Labels

```typescript
export const CATEGORY_LABELS: Record<Category, string> = {
  voice_memo: 'Voice Memo',
  meeting_notes: 'Meeting Notes',
  // ... other categories ...
  documentation: 'Documentation',
  my_new_category: 'My New Category',  // Add this line
}
```

#### 3.2 Short Labels (for mobile)

```typescript
export const CATEGORY_LABELS_SHORT: Record<Category, string> = {
  voice_memo: 'Memo',
  meeting_notes: 'Meeting',
  // ... other categories ...
  documentation: 'Docs',
  my_new_category: 'NewCat',  // Add this line (keep it short!)
}
```

#### 3.3 Category List

```typescript
export const ALL_CATEGORIES: Category[] = [
  'voice_memo',
  'meeting_notes',
  // ... other categories ...
  'documentation',
  'my_new_category',  // Add this line
]
```

### 4. Add CSS Styling for Category Badge

**File:** `/frontend/src/index.css`

Add CSS styles for your category badge in both dark and light modes:

```css
/* Add after existing category styles */

/* Dark mode */
:root .category-my-new-category {
  background: rgba(147, 51, 234, 0.15);  /* Choose your color */
  color: #A78BFA;                         /* Text color */
  border: 1px solid rgba(147, 51, 234, 0.3);
}

/* Light mode */
.light .category-my-new-category {
  background: rgba(147, 51, 234, 0.10);
  color: #7C3AED;
  border: 1px solid rgba(147, 51, 234, 0.25);
}
```

**Color Palette Suggestions:**
- Blue: `rgba(59, 130, 246, ...)` (#3B82F6)
- Purple: `rgba(147, 51, 234, ...)` (#9333EA)
- Pink: `rgba(236, 72, 153, ...)` (#EC4899)
- Orange: `rgba(249, 115, 22, ...)` (#F97316)
- Green: `rgba(34, 197, 94, ...)` (#22C55E)
- Yellow: `rgba(234, 179, 8, ...)` (#EAB308)
- Red: `rgba(239, 68, 68, ...)` (#EF4444)

### 5. Rebuild and Deploy

After making all changes:

#### Backend:
```bash
cd backend
podman build -t echonote-backend:latest -f Containerfile .
podman restart echonote-backend
```

#### Frontend:
```bash
cd frontend
podman build -t echonote-frontend:latest -f Containerfile .
podman restart echonote-frontend
```

Or restart the entire stack:
```bash
podman-compose restart
```

### 6. Verify the Changes

1. **Frontend:** Open the application and create a new transcription
2. **Check dropdown:** The new category should appear in the category selector
3. **Test filtering:** Filter transcriptions by your new category
4. **Verify badge:** The category badge should display with correct colors
5. **Test API:** Check that the category is saved correctly in the database

## Database Considerations

**No migration required!** The `category` field in the database is a string column that accepts any value from the enum. Adding new categories doesn't require a database migration.

However, existing transcriptions will not automatically be categorized with your new category. They will retain their current category values.

## Example: Adding "Podcast Notes" Category

### Backend (`models.py`):
```python
PODCAST_NOTES = "podcast_notes"
```

### Frontend (`types.ts`):
```typescript
| 'podcast_notes'
```

### Labels (`categoryUtils.ts`):
```typescript
podcast_notes: 'Podcast Notes',        // Full label
podcast_notes: 'Podcast',              // Short label
'podcast_notes',                       // In ALL_CATEGORIES array
```

### CSS (`index.css`):
```css
/* Dark mode */
:root .category-podcast-notes {
  background: rgba(168, 85, 247, 0.15);
  color: #C084FC;
  border: 1px solid rgba(168, 85, 247, 0.3);
}

/* Light mode */
.light .category-podcast-notes {
  background: rgba(168, 85, 247, 0.10);
  color: #9333EA;
  border: 1px solid rgba(168, 85, 247, 0.25);
}
```

## Troubleshooting

### Category not appearing in dropdown
- Check that the category is added to `ALL_CATEGORIES` array
- Verify frontend container was rebuilt
- Clear browser cache

### API returns validation error
- Ensure backend enum value matches frontend type exactly
- Rebuild backend container
- Check backend logs for validation errors

### Badge has wrong color or no styling
- Verify CSS class name follows pattern: `category-{value-with-dashes}`
  - Example: `podcast_notes` → `category-podcast-notes`
- Check that both dark and light mode styles are defined
- Clear browser cache and rebuild frontend

### TypeScript compilation errors
- Ensure the category is added to the TypeScript union type
- Run `npm run build` in frontend directory to check for type errors
- Make sure labels in `CATEGORY_LABELS` match the type exactly

## Best Practices

1. **Naming Convention:**
   - Backend: `UPPER_SNAKE_CASE` (enum key), `lower_snake_case` (enum value)
   - Frontend: `lower_snake_case` everywhere
   - CSS: `category-with-dashes`

2. **Label Guidelines:**
   - Full labels: Use proper capitalization (e.g., "Meeting Notes")
   - Short labels: Keep under 10 characters for mobile display
   - Be descriptive but concise

3. **Color Selection:**
   - Choose colors that are distinct from existing categories
   - Ensure good contrast in both dark and light modes
   - Test accessibility with color-blind simulators if possible

4. **Testing:**
   - Test category selection on both desktop and mobile
   - Verify filtering works correctly
   - Check that category persists after page refresh
   - Test with existing transcriptions

## File Checklist

Before rebuilding, verify you've updated all these files:

- [ ] `/backend/models.py` - Category enum
- [ ] `/frontend/src/types.ts` - TypeScript type
- [ ] `/frontend/src/utils/categoryUtils.ts` - Labels (3 places)
- [ ] `/frontend/src/index.css` - CSS styles (2 modes)
- [ ] Rebuild backend container
- [ ] Rebuild frontend container
- [ ] Test in browser

## Need Help?

If you encounter issues:
1. Check backend logs: `podman logs echonote-backend`
2. Check frontend logs: `podman logs echonote-frontend`
3. Verify all enum values match exactly (case-sensitive)
4. Ensure containers were rebuilt after code changes

---

**Last Updated:** December 4, 2025
**EchoNote Version:** 1.0
