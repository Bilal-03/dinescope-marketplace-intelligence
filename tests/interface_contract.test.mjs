import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';

const source = await readFile(new URL('../app/components/dashboard.tsx', import.meta.url), 'utf8');
const styles = await readFile(new URL('../app/globals.css', import.meta.url), 'utf8');

test('primary navigation and Decision Lab controls have accessible names', () => {
  assert.match(source, /<nav aria-label="Primary navigation">/);
  assert.match(source, /aria-label=\{item\.label\}/);
  assert.match(source, /aria-label="Decision minimum allocated transactions"/);
  assert.match(source, /aria-label="Scenario name"/);
  assert.match(source, /aria-label="Compare current lab with"/);
  assert.match(source, /aria-current=\{page === item\.id \? 'page' : undefined\}/);
  assert.match(source, /aria-pressed=\{metric === 'orders'\}/);
  assert.match(source, /aria-live="polite"/);
  assert.match(source, /role="dialog" aria-modal="true" aria-labelledby="method-title"/);
});

test('all buttons declare their type and table selection is keyboard operable', () => {
  const buttonCount = (source.match(/<button\b/g) ?? []).length;
  const typedButtonCount = (source.match(/type="button"/g) ?? []).length;
  assert.ok(buttonCount > 20);
  assert.equal(typedButtonCount, buttonCount, 'every button must declare type="button"');
  assert.match(source, /tabIndex=\{0\} onClick=\{\(\) => setSelectedMarket\(row\.market\)\}/);
  assert.match(source, /tabIndex=\{0\} onClick=\{\(\) => setSelectedKey\(key\)\}/);
  assert.match(source, /event\.key === 'Enter' \|\| event\.key === ' '/);
  assert.match(source, /aria-label=\{`\$\{marketName\} \$\{cuisine\}: .*allocated transactions`\}/);
});

test('decision presets and evidence exports remain device-local and explicit', () => {
  assert.match(source, /localStorage\.getItem\('platelens-decision-scenarios'\)/);
  assert.match(source, /localStorage\.setItem\('platelens-decision-scenarios'/);
  assert.match(source, /new Blob\(\[csv\], \{ type: 'text\/csv;charset=utf-8' \}\)/);
  assert.match(source, /platelens-decision-brief-/);
});

test('keyboard focus treatment is visible for controls and selectable rows', () => {
  assert.match(styles, /button:focus-visible, select:focus-visible, input:focus-visible/);
  assert.match(styles, /market-table tbody tr:focus-visible, \.cuisine-table tbody tr:focus-visible/);
});
