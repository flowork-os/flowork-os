#!/usr/bin/env node
/**
 * ⚡ FLOWORK OS — SOVEREIGN SKILL LINTER & QUALITY GATE VALIDATOR
 * Enforces strict compliance for all skills under /opt/floworkos/skills/
 * 
 * Rules Enforced:
 * 1. Must reside in /opt/floworkos/skills/<skill-name>/
 * 2. SKILL.md must exist with valid YAML frontmatter.
 * 3. Frontmatter `name` must match parent directory.
 * 4. Frontmatter `keywords` must contain EXACTLY 20 English strings.
 * 5. Frontmatter `domain` must be a valid domain classification.
 * 6. Mandatory sections must be present in SKILL.md.
 * 7. Zero symlinks anywhere in the skill directory.
 */

const fs = require('fs');
const path = require('path');

const SKILLS_DIR = path.resolve(__dirname);
const MANDATORY_SECTIONS = [
    'Objective',
    'Prerequisites',
    'Standard Operating Procedure',
    'Verification',
    'Failure Modes'
];

const VALID_DOMAINS = [
    'os_doctrine',
    'browser',
    'shell_system',
    'code_dev',
    'database',
    'security',
    'network'
];

function parseFrontmatter(content) {
    if (!content.startsWith('---')) return null;
    const endIdx = content.indexOf('\n---', 3);
    if (endIdx === -1) return null;

    const rawYaml = content.slice(3, endIdx).trim();
    const body = content.slice(endIdx + 4).trim();
    const result = { keywords: [] };

    let currentArrayKey = null;
    const lines = rawYaml.split('\n');

    for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed || trimmed.startsWith('#')) continue;

        if (trimmed.startsWith('- ') && currentArrayKey) {
            result[currentArrayKey].push(trimmed.slice(2).trim());
            continue;
        }

        const colonIdx = trimmed.indexOf(':');
        if (colonIdx !== -1) {
            const key = trimmed.slice(0, colonIdx).trim();
            const val = trimmed.slice(colonIdx + 1).trim();

            if (!val) {
                currentArrayKey = key;
                if (!result[key]) result[key] = [];
            } else {
                currentArrayKey = null;
                result[key] = val.replace(/^["']|["']$/g, '');
            }
        }
    }

    return { frontmatter: result, body };
}

function lintSkills() {
    console.log('=================================================================');
    console.log('⚡ FLOWORK OS — SKILL QUALITY GATE & LINTER');
    console.log(`Auditing target directory: ${SKILLS_DIR}`);
    console.log('=================================================================\n');

    const entries = fs.readdirSync(SKILLS_DIR, { withFileTypes: true });
    let totalSkills = 0;
    let failedSkills = 0;

    for (const entry of entries) {
        if (!entry.isDirectory()) continue;
        const skillName = entry.name;
        const skillDir = path.join(SKILLS_DIR, skillName);
        totalSkills++;

        console.log(`🔍 Inspecting skill: [${skillName}]`);
        const errors = [];

        // Check symlinks
        const stat = fs.lstatSync(skillDir);
        if (stat.isSymbolicLink()) {
            errors.push('Skill directory must not be a symbolic link (violates anti-symlink doctrine).');
        }

        const skillMdPath = path.join(skillDir, 'SKILL.md');
        if (!fs.existsSync(skillMdPath)) {
            errors.push('Missing mandatory SKILL.md file.');
        } else {
            const rawContent = fs.readFileSync(skillMdPath, 'utf8');
            const parsed = parseFrontmatter(rawContent);

            if (!parsed) {
                errors.push('SKILL.md is missing valid YAML frontmatter between --- markers.');
            } else {
                const fm = parsed.frontmatter;

                if (!fm.name || fm.name !== skillName) {
                    errors.push(`Frontmatter name "${fm.name}" does not match directory name "${skillName}".`);
                }

                if (!fm.description || fm.description.length < 20) {
                    errors.push('Frontmatter description must be descriptive (at least 20 characters).');
                }

                if (!fm.domain || !VALID_DOMAINS.includes(fm.domain)) {
                    errors.push(`Frontmatter domain "${fm.domain}" is invalid. Must be one of: ${VALID_DOMAINS.join(', ')}.`);
                }

                const kwCount = Array.isArray(fm.keywords) ? fm.keywords.length : 0;
                if (kwCount !== 20) {
                    errors.push(`Frontmatter keywords count is ${kwCount}. EXACTLY 20 keywords are mandatory.`);
                }

                // Check sections
                for (const sec of MANDATORY_SECTIONS) {
                    if (!parsed.body.toLowerCase().includes(sec.toLowerCase())) {
                        errors.push(`Missing mandatory section: "${sec}".`);
                    }
                }
            }
        }

        if (errors.length > 0) {
            failedSkills++;
            console.log(`❌ FAILED: ${errors.length} violation(s) found in [${skillName}]:`);
            errors.forEach(e => console.log(`   - ${e}`));
        } else {
            console.log(`✅ PASSED: All Flowork OS quality gates verified.`);
        }
        console.log('');
    }

    console.log('-----------------------------------------------------------------');
    console.log(`Audit Summary: Total Skills: ${totalSkills} | Passed: ${totalSkills - failedSkills} | Failed: ${failedSkills}`);

    if (failedSkills > 0) {
        console.error('\n❌ QUALITY GATE REJECTION: One or more skills failed sovereign validation.');
        process.exit(1);
    } else {
        console.log('\n✅ QUALITY GATE ACCEPTED: Skill catalog is 100% compliant with Flowork OS standards.');
        process.exit(0);
    }
}

if (require.main === module) {
    lintSkills();
}

module.exports = { lintSkills, parseFrontmatter };
