import { describe, expect, it, vi } from 'vitest';
import { fetchPlayerProfile, fetchSeasonDates, seasonProgress } from './espn';

describe('season timeline', () => {
  it('calculates elapsed time, clamps outside dates and rejects invalid intervals', () => {
    const start = '2026-10-20T07:00:00Z', end = '2027-06-26T07:00:00Z';
    const first = Date.parse(start), last = Date.parse(end);
    expect(seasonProgress(start, end, first - 1)).toBe(0);
    expect(seasonProgress(start, end, (first + last) / 2)).toBe(50);
    expect(seasonProgress(start, end, last + 1)).toBe(100);
    expect(() => seasonProgress(end, start, first)).toThrow('Invalid');
  });
  it('uses the regular-season start and postseason end for the selected season', async () => {
    const request = vi.spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce(Response.json({startDate:'2026-10-20T07:00:00Z'}))
      .mockResolvedValueOnce(Response.json({endDate:'2027-06-26T06:59:00Z'}));
    try {
      expect(await fetchSeasonDates('2026-27')).toEqual({start:'2026-10-20T07:00:00Z',end:'2027-06-26T06:59:00Z'});
      expect(request.mock.calls.map(call => String(call[0]))).toEqual([
        expect.stringContaining('/seasons/2027/types/2'), expect.stringContaining('/seasons/2027/types/3'),
      ]);
      await expect(fetchSeasonDates('2026-29')).rejects.toThrow('Unrecognized');
    } finally { request.mockRestore(); }
  });
  it('rejects mismatched player profiles', async () => {
    const request = vi.spyOn(globalThis,'fetch').mockResolvedValue(Response.json({id:'2'}));
    try { await expect(fetchPlayerProfile('1')).rejects.toThrow('different player'); }
    finally { request.mockRestore(); }
  });
});
