# Delete Functionality UI Guide

## Visual Overview

### Expense History Page with Delete Features

```
┌─────────────────────────────────────────────────────────────────┐
│ 🏠 Expense History                                    [+ Add Expense] │
├─────────────────────────────────────────────────────────────────┤
│ 🔍 Search & Filter                                              │
│ [Search Box] [Category ▼] [Min $] [Max $] [🔍]                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ 📋 Your Expenses                                    [42 total] │
├─────────────────────────────────────────────────────────────────┤
│ ⚠️  2 expense(s) selected                                      │
│ [☑️ Select All] [☐ Clear Selection] [🗑️ Delete Selected]        │
├─────────────────────────────────────────────────────────────────┤
│ [☑️] │ Description      │ Category │ Amount │ Confidence │ Date │ Actions │
├─────┼─────────────────┼──────────┼────────┼────────────┼──────┼─────────┤
│ [☑️] │ Starbucks Coffee │ Dining   │ $4.50  │ ████ 85%   │ Today│ 👁️ ✏️ 🗑️ │
│ [☐] │ Uber Ride       │ Transport│ $12.30 │ ███ 92%    │ Today│ 👁️ ✏️ 🗑️ │
│ [☑️] │ Grocery Store   │ Food     │ $45.67 │ ████ 88%   │ Today│ 👁️ ✏️ 🗑️ │
│ [☐] │ Gas Station     │ Transport│ $35.00 │ ███ 90%    │ Today│ 👁️ ✏️ 🗑️ │
└─────┴─────────────────┴──────────┴────────┴────────────┴──────┴─────────┘
```

## Key UI Elements

### 1. **Checkbox Column**
- ☑️ Individual checkboxes for each expense
- ☑️ Master checkbox in header for "Select All"
- Visual highlighting of selected rows

### 2. **Bulk Actions Bar**
```
┌─────────────────────────────────────────────────────────────────┐
│ ⚠️  3 expense(s) selected                                      │
│ [☑️ Select All] [☐ Clear Selection] [🗑️ Delete Selected]        │
└─────────────────────────────────────────────────────────────────┘
```
- Appears only when expenses are selected
- Shows count of selected items
- Quick action buttons

### 3. **Individual Delete Button**
```
Actions: [👁️ View] [✏️ Edit] [🗑️ Delete]
```
- Red trash icon for each expense
- Triggers individual delete confirmation

## Modal Dialogs

### Individual Delete Confirmation
```
┌─────────────────────────────────────────────────────────────────┐
│ ⚠️  Confirm Deletion                                      [✕]   │
├─────────────────────────────────────────────────────────────────┤
│ Are you sure you want to delete this expense?                  │
│                                                                 │
│ ℹ️  Description: Starbucks Coffee - Downtown Location          │
│                                                                 │
│ ⚠️  This action cannot be undone.                              │
├─────────────────────────────────────────────────────────────────┤
│                                    [Cancel] [🗑️ Delete Expense] │
└─────────────────────────────────────────────────────────────────┘
```

### Bulk Delete Confirmation
```
┌─────────────────────────────────────────────────────────────────┐
│ ⚠️  Confirm Bulk Deletion                                 [✕]   │
├─────────────────────────────────────────────────────────────────┤
│ Are you sure you want to delete the selected expenses?         │
│                                                                 │
│ ⚠️  Selected expenses: 3                                       │
│ • Starbucks Coffee - Downtown Location                         │
│ • Grocery Store - Weekly Shopping                              │
│ • Gas Station - Shell                                          │
│                                                                 │
│ ⚠️  This action cannot be undone.                              │
├─────────────────────────────────────────────────────────────────┤
│                           [Cancel] [🗑️ Delete Selected Expenses] │
└─────────────────────────────────────────────────────────────────┘
```

## Visual States

### 1. **No Selection State**
- Bulk actions bar is hidden
- Only individual delete buttons visible
- Normal row appearance

### 2. **Selection State**
- Selected rows highlighted in light blue
- Bulk actions bar appears
- Selection count updates dynamically

### 3. **Loading State**
```
[🔄 Deleting...] (button disabled during operation)
```

## Responsive Design

### Desktop View
- Full table with all columns visible
- Bulk actions bar spans full width
- Large, easy-to-click buttons

### Mobile View
- Condensed table layout
- Stacked information for each expense
- Touch-friendly checkboxes and buttons

## Accessibility Features

### Screen Reader Support
- Proper ARIA labels for all interactive elements
- Descriptive text for delete actions
- Clear focus indicators

### Keyboard Navigation
- Tab through all interactive elements
- Space bar to toggle checkboxes
- Enter to activate buttons

## Color Coding

### Visual Indicators
- 🔵 **Blue**: Selected rows (light blue background)
- 🔴 **Red**: Delete buttons and warnings
- 🟡 **Yellow**: Warning messages and confirmations
- 🟢 **Green**: Success messages after deletion

## User Flow

### Individual Delete Flow
1. User clicks 🗑️ delete icon
2. Confirmation modal appears
3. User confirms deletion
4. Expense is removed
5. Success message shown

### Bulk Delete Flow
1. User selects expenses with checkboxes
2. Bulk actions bar appears
3. User clicks "Delete Selected"
4. Bulk confirmation modal appears
5. User reviews and confirms
6. All selected expenses removed
7. Success message shown

## Error Handling

### Error Messages
```
┌─────────────────────────────────────────────────────────────────┐
│ ❌ Error: Failed to delete expenses. Please try again.          │
└─────────────────────────────────────────────────────────────────┘
```

### Network Issues
```
┌─────────────────────────────────────────────────────────────────┐
│ ⚠️  Connection error. Please check your internet and try again. │
└─────────────────────────────────────────────────────────────────┘
```

This UI design provides an intuitive, safe, and efficient way for users to manage their expense deletions with clear visual feedback and comprehensive safety measures.