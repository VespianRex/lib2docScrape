/**
 * Simple test to verify GUI test environment
 */

import { describe, it, expect } from 'bun:test';
import './setup-bun.js';

describe('GUI Test Environment', () => {
  it('should be able to run basic tests', () => {
    expect(1 + 1).toBe(2);
  });

  it('should have access to DOM APIs', () => {
    // Check if we can create basic DOM elements
    const div = document.createElement('div');
    div.textContent = 'Test';
    expect(div.textContent).toBe('Test');
  });
});
