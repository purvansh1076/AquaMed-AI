/**
 * Test-only authentication helpers.
 * =================================
 * The application rejects malformed or expired JWTs during session
 * rehydration, so tests must persist JWT-shaped tokens rather than arbitrary
 * placeholder strings. These tokens are unsigned and never reach production.
 */

import type { IdentityResponse } from '../types/api';

function base64UrlEncode(value: unknown): string {
  return btoa(JSON.stringify(value))
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=+$/, '');
}

/** Build a JWT-shaped token with a controlled `exp` claim. */
export function makeTestJwt(expiresInSeconds = 3600): string {
  const now = Math.floor(Date.now() / 1000);
  return [
    base64UrlEncode({ alg: 'HS256', typ: 'JWT' }),
    base64UrlEncode({
      sub: 'test_expert',
      role: 'expert',
      iat: now,
      exp: now + expiresInSeconds,
    }),
    'test-signature',
  ].join('.');
}

/** Minimal backend identity response used to mock `api.getIdentity()`. */
export function mockExpertIdentity(): IdentityResponse {
  return {
    sub: 'test_expert',
    role: 'expert',
    email: 'expert@aquamedi.gov.in',
    full_name: 'Test Expert',
    department: 'Department of Agriculture & Water Resources',
    permissions: ['farmer:*', 'expert:*'],
    is_authenticated: true,
  };
}
