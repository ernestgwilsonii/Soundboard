# Initial Concept
The Soundboard Website is a Flask-based platform for creating, customizing, and sharing soundboards, featuring robust account management for users and administrators.

# Product Guide - Soundboard Website

## Vision
The Soundboard Website is a professional and intuitive platform that empowers users to create, manage, and share personalized soundboards. It serves as a versatile tool for casual entertainment and content creation, supported by a secure and horizontally scalable distributed architecture.

## Target Audience
- **Casual Users:** Individuals looking for a fun and easy way to organize and play their favorite sounds.
- **Content Creators & Streamers:** Professionals who need a reliable interface for triggering sound effects during live sessions.
- **Administrators:** System managers who oversee user activity and maintain the platform's integrity.

## Core Goals
- **Seamless Interaction:** Provide a highly responsive and lag-free audio playback experience directly in the browser.
- **Creative Freedom:** Offer robust tools for users to upload custom audio files and personalize their boards with a diverse icon library.
- **Trust and Security:** Implement industry-standard security measures for account protection and comprehensive administrative management.

## Key Features
- **Dynamic Soundboards:** Interactive grids where icons trigger high-quality audio playback.
- **Personalized Management:** Secure user accounts with flexible login (username or email), verified email addresses, rich profiles (bios and social links), custom avatars, password recovery, account deactivation, and the ability to create, edit (including drag-and-drop reordering and advanced playback settings), delete, and favorite soundboards.
- **Complete Data Portability:** Export and import complete "Soundboard Packs" (.sbp) containing all audio assets, custom icons, and playback configurations.
- **Custom Playlists:** Create and manage ordered collections of sounds from any soundboard, with support for sequential, shuffled, and looped playback.
- **Public Identity:** Dedicated public profile pages showcasing user bios, social connectivity, and shared content.
- **Administrative Control:** Advanced tools for user role management, account moderation, featured content curation, global announcements, and system maintenance mode.
- **Enhanced Discovery:** A dynamic sidebar, "Browse Members" list, and "Featured" section to easily find personal favorites and explore community content.
- **Social Engagement:** Quick-share capability for public soundboards.
- **Community Interaction:** Integrated star-rating system, comments, user following system, and real-time in-app notifications for social engagement, powered by a distributed Redis-based synchronization engine.
- **Community Feed:** A real-time activity feed on the home page highlighting recent creations and community actions.
- **Intelligent Organization:** Comprehensive tagging system for soundboards, enabling users to categorize content and discover popular themes via tag-based search and navigation.
- **Advanced Playback Control:** Per-sound customization including volume normalization, looping, visual waveform trimming (WaveSurfer.js), keyboard hotkeys, and custom visual themes for individual soundboards. Advanced search filtering by name, rating, and recency.
- **AI-Ready Architecture:** Automated audio normalization and metadata generation pipeline during content ingestion.
- **Hardened Security:** Mandatory email verification for new accounts, secure token-based password resets, automatic account lockout, and IP-based rate limiting. Continuously protected by automated Static Application Security Testing (SAST) and Software Composition Analysis (SCA) to identify vulnerabilities and outdated dependencies.
- **Self-Verifying Architecture:** Robust E2E automation suite (Playwright) ensuring every user flow—from auth to visual trimming—is verified on every change.
- **Standardized Excellence:** Strict adherence to PEP 8, PEP 257, and type safety, combined with a core philosophy that human-readable, self-documenting code is paramount. This is enforced by modular architecture and a comprehensive suite of automated quality gates.
- **Responsive Design:** A polished, professional UI that adapts perfectly to desktop and mobile environments, including custom-themed error pages.