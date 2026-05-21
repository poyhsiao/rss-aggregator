# Learnings - Backup/Restore Feature

## Error Handling Best Practices

### Import Backup Error Handling
- **Issue**: Generic error messages don't help users understand what went wrong
- **Solution**: Always capture and display actual error messages from API responses
- **Pattern**: Use `error instanceof Error ? error.message : String(error)` to safely extract error messages
- **Location**: BackupManager.vue lines 133-136

### Error Message Display
- Show specific error messages from `result.message` when available
- Fall back to generic message only when no specific error is available
- This improves user experience by providing actionable feedback

## Component Organization

### Moving Features Between Components
- **Issue**: "Open data folder" button was in SettingsPage but better suited for DebugDialog
- **Solution**: Move desktop-specific debugging features to DebugDialog component
- **Benefit**: Better separation of concerns - settings vs debugging tools
- **Files Modified**: SettingsPage.vue, DebugDialog.vue

### Import Cleanup
- When removing a feature, also remove:
  - Unused imports (e.g., `FolderOpen` icon, `openDataFolder` function)
  - Unused handler functions
  - This keeps code clean and reduces bundle size

## Dialog Management

### Restart Backend Dialog
- **Pattern**: Show dialog after successful import to prompt user to restart backend
- **Implementation**: 
  - Add ref for dialog visibility (`showRestartDialog`)
  - Show dialog only for desktop app (`isDesktop.value`)
  - Add handler function to restart backend
  - Include proper icon (RefreshCw) and button styling
- **Location**: BackupManager.vue lines 109-138, 311-324

### Dialog Best Practices
- Use consistent dialog structure with title, description, and action buttons
- Include cancel button for user choice
- Use proper icons for actions (RefreshCw for restart)
- Follow existing dialog patterns in the codebase

## Desktop-Specific Features

### Conditional Rendering
- Use `isTauri()` to check if running in desktop environment
- Only show desktop-specific features when appropriate
- Example: "Open data folder" and "Open DevTools" buttons only in Tauri

### Tauri Bridge Functions
- Import from `@/utils/tauri-bridge` for desktop-specific functions
- Functions available: `openDataFolder`, `restartBackend`, `toggleDevtools`
- Always wrap in try-catch for error handling
- Show user-friendly error messages via toast

## Code Quality

### TypeScript Best Practices
- Use proper type imports: `import type { BackupPreview, ExportOptions, ImportResult }`
- Maintain strict type checking - no `any` types
- Use computed properties for derived values
- Use refs for reactive state

### Vue 3 Composition API
- Use `<script setup>` syntax
- Properly organize code: imports, refs, computed, functions, template
- Use proper icon imports from lucide-vue-next
- Follow existing code patterns and styling conventions

## Testing Considerations

### Error Scenarios
- Test import with invalid backup files
- Test import with corrupted data
- Verify error messages are displayed correctly
- Test restart backend functionality

### Desktop vs Web
- Test features in both desktop (Tauri) and web environments
- Verify conditional rendering works correctly
- Test desktop-specific dialogs and buttons

## Future Improvements

### Potential Enhancements
- Add progress indicator for large imports
- Show detailed import statistics
- Add validation before import
- Support for incremental backups
- Auto-restart option after import

### Code Organization
- Consider extracting dialog components for reusability
- Create composable for dialog management
- Consolidate error handling patterns
