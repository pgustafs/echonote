/**
 * Category selector component for transcriptions
 * Used in both desktop and mobile views
 */

import { Category } from '../types'
import { CATEGORY_LABELS, getCategoryClassName, ALL_CATEGORIES } from '../utils/categoryUtils'

interface CategorySelectorProps {
  value: Category
  onChange: (category: Category) => void
  disabled?: boolean
  isMobile?: boolean
  showLabel?: boolean
  showBadge?: boolean
}

export default function CategorySelector({
  value,
  onChange,
  disabled = false,
  isMobile = false,
  showLabel = true,
  showBadge = false,
}: CategorySelectorProps) {
  return (
    <div className={isMobile ? "section-container-mobile" : "section-container"}>
      <div className="flex flex-col sm:flex-row sm:items-center gap-3">
        {showLabel && (
          <label className="text-sm font-medium text-text-primary flex items-center space-x-2">
            <svg className="w-4 h-4 text-accent-blue" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
            </svg>
            <span>Category</span>
          </label>
        )}
        <div className="flex items-center gap-2">
          <select
            value={value}
            onChange={(e) => onChange(e.target.value as Category)}
            disabled={disabled}
            className={isMobile ? "select-field select-field-mobile py-2 text-sm min-h-[44px]" : "select-field py-2 text-sm min-h-[44px]"}
            onClick={(e) => e.stopPropagation()}
          >
            {ALL_CATEGORIES.map((category) => (
              <option key={category} value={category}>
                {CATEGORY_LABELS[category]}
              </option>
            ))}
          </select>
          {showBadge && (
            <span className={getCategoryClassName(value)}>
              {CATEGORY_LABELS[value]}
            </span>
          )}
        </div>
      </div>
    </div>
  )
}
