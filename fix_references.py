#!/usr/bin/env python3

import re

# Read the file
with open('fantasy_draft_assistant_v2_clean.py', 'r') as f:
    content = f.read()

# Replace the file references
replacements = [
    ('FantasyPros_Fantasy_Football_Projections_QB (1).csv', 'FantasyPros_Fantasy_Football_Projections_QB.csv'),
    ('FantasyPros_Fantasy_Football_Projections_RB (2).csv', 'FantasyPros_Fantasy_Football_Projections_RB.csv'),
    ('FantasyPros_Fantasy_Football_Projections_WR (1).csv', 'FantasyPros_Fantasy_Football_Projections_WR.csv'),
    ('FantasyPros_Fantasy_Football_Projections_TE (2) (1).csv', 'FantasyPros_Fantasy_Football_Projections_TE.csv'),
]

for old, new in replacements:
    content = content.replace(old, new)

# Write the fixed file
with open('fantasy_draft_assistant_v2.py', 'w') as f:
    f.write(content)

print("File references fixed successfully!") 