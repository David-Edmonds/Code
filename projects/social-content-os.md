# Social Content OS Blueprint

## Goal

Manage grow_goodness, CultureRankHQ, and future brands from one review-first workflow without duplicate posts or constant manual copying.

## Minimum record model

- Brand
- Content ID
- Series/content type
- Topic
- Master concept
- Channel-specific caption
- Asset status and URL
- Approval status
- Due date and target time
- Scheduled status and platform record ID
- Published URL
- Error/retry note
- Performance snapshot

## First validated workflow

1. David or ChatGPT creates a draft record.
2. The asset and captions are reviewed.
3. David changes status to `Approved`.
4. A scheduled workflow finds approved items due today.
5. Buffer schedules supported channels.
6. The record is updated with scheduled IDs and status.
7. Failures are recorded and surfaced; they are not silently retried into duplicates.

## Do not build yet

- A custom dashboard before Airtable/Buffer fields and statuses are proven
- Fully autonomous approval
- Duplicate scheduling across Buffer and Publer for the same channel
- Performance AI that lacks reliable source metrics
