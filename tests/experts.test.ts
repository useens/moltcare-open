import { describe, it, expect, vi } from 'vitest';
import { BaseExpert, ExpertProfile, ExpertInput } from '../src/multi-expert/experts/base-expert';
import { ResearcherExpert } from '../src/multi-expert/experts/researcher';
import { ArchitectExpert } from '../src/multi-expert/experts/architect';
import { EngineerExpert } from '../src/multi-expert/experts/engineer';
import { CaptainExpert } from '../src/multi-expert/experts/captain';

describe('Multi-Expert System', () => {
  describe('BaseExpert', () => {
    it('should create expert with profile', () => {
      const profile: ExpertProfile = {
        id: 'test',
        name: 'Test Expert',
        role: 'Tester',
        expertise: ['testing'],
        personality: 'thorough'
      };
      
      const expert = new BaseExpert(profile);
      expect(expert.getProfile()).toEqual(profile);
    });

    it('should generate system prompt', () => {
      const profile: ExpertProfile = {
        id: 'test',
        name: 'Test Expert',
        role: 'Tester',
        expertise: ['testing', 'qa'],
        personality: 'thorough'
      };
      
      const expert = new BaseExpert(profile);
      const prompt = expert.generateSystemPrompt();
      
      expect(prompt).toContain('Test Expert');
      expect(prompt).toContain('Tester');
      expect(prompt).toContain('testing');
      expect(prompt).toContain('qa');
    });

    it('should format input correctly', () => {
      const profile: ExpertProfile = {
        id: 'test',
        name: 'Test Expert',
        role: 'Tester',
        expertise: ['testing'],
        personality: 'thorough'
      };
      
      const expert = new BaseExpert(profile);
      const input: ExpertInput = {
        topic: 'test topic',
        context: { key: 'value' },
        previousRounds: [],
        currentRound: 1,
        maxRounds: 3
      };
      
      const formatted = expert.formatInput(input);
      expect(formatted).toContain('test topic');
      expect(formatted).toContain('key');
      expect(formatted).toContain('value');
    });
  });

  describe('ResearcherExpert', () => {
    it('should create researcher with correct profile', () => {
      const researcher = new ResearcherExpert();
      const profile = researcher.getProfile();
      
      expect(profile.id).toBe('researcher');
      expect(profile.name).toBe('研究员');
      expect(profile.role).toBe('Researcher');
      expect(profile.expertise).toContain('数据验证');
    });

    it('should analyze and return opinion', async () => {
      const researcher = new ResearcherExpert();
      const input: ExpertInput = {
        topic: 'test',
        context: {},
        previousRounds: [],
        currentRound: 1,
        maxRounds: 3
      };
      
      const opinion = await researcher.think(input);
      expect(opinion).toHaveProperty('opinion');
      expect(opinion).toHaveProperty('confidence');
      expect(opinion).toHaveProperty('concerns');
      expect(opinion.expertId).toBe('researcher');
    });
  });

  describe('ArchitectExpert', () => {
    it('should create architect with correct profile', () => {
      const architect = new ArchitectExpert();
      const profile = architect.getProfile();
      
      expect(profile.id).toBe('architect');
      expect(profile.name).toBe('架构师');
      expect(profile.role).toBe('Architect');
      expect(profile.expertise).toContain('系统设计');
    });

    it('should analyze and return opinion', async () => {
      const architect = new ArchitectExpert();
      const input: ExpertInput = {
        topic: 'system design',
        context: {},
        previousRounds: [],
        currentRound: 1,
        maxRounds: 3
      };
      
      const opinion = await architect.think(input);
      expect(opinion).toHaveProperty('opinion');
      expect(opinion).toHaveProperty('confidence');
      expect(opinion.expertId).toBe('architect');
    });
  });

  describe('EngineerExpert', () => {
    it('should create engineer with correct profile', () => {
      const engineer = new EngineerExpert();
      const profile = engineer.getProfile();
      
      expect(profile.id).toBe('engineer');
      expect(profile.name).toBe('工程师');
      expect(profile.role).toBe('Engineer');
      expect(profile.expertise).toContain('实现可行性评估');
    });

    it('should analyze and return opinion with cost estimate', async () => {
      const engineer = new EngineerExpert();
      const input: ExpertInput = {
        topic: 'implementation',
        context: {},
        previousRounds: [],
        currentRound: 1,
        maxRounds: 3
      };
      
      const opinion = await engineer.think(input);
      expect(opinion).toHaveProperty('opinion');
      expect(opinion).toHaveProperty('confidence');
      expect(opinion.expertId).toBe('engineer');
    });
  });

  describe('CaptainExpert', () => {
    it('should create captain with correct profile', () => {
      const captain = new CaptainExpert();
      const profile = captain.getProfile();
      
      expect(profile.id).toBe('captain');
      expect(profile.name).toBe('队长');
      expect(profile.role).toBe('Captain');
      expect(profile.expertise).toContain('决策整合');
    });

    it('should synthesize opinions and make decision', async () => {
      const captain = new CaptainExpert();
      const input: ExpertInput = {
        topic: 'final decision',
        context: {
          opinions: [
            { expertId: 'researcher', content: 'data is good', confidence: 0.8 },
            { expertId: 'architect', content: 'design works', confidence: 0.9 }
          ]
        },
        previousRounds: [
          {
            roundNumber: 1,
            opinions: [
              { 
                expertId: 'researcher', 
                expertName: '研究员',
                opinion: 'data is good', 
                keyPoints: ['数据验证通过'],
                confidence: 0.8 
              },
              { 
                expertId: 'architect', 
                expertName: '架构师',
                opinion: 'design works', 
                keyPoints: ['设计可行'],
                confidence: 0.9 
              }
            ]
          }
        ],
        currentRound: 3,
        maxRounds: 3
      };
      
      const opinion = await captain.think(input);
      expect(opinion).toHaveProperty('opinion');
      expect(opinion).toHaveProperty('confidence');
      expect(opinion.expertId).toBe('captain');
    });
  });
});
