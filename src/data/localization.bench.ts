import { bench, describe } from 'vitest';
import { resolveSuggestedLanguages } from './localization';

describe('resolveSuggestedLanguages', () => {
  bench('resolveSuggestedLanguages with match', () => {
    resolveSuggestedLanguages('tr-TR');
  });
  bench('resolveSuggestedLanguages without match', () => {
    resolveSuggestedLanguages('es-ES');
  });
});
