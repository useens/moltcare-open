import { describe, it, expect, vi } from 'vitest';
import { ExpertOrchestrator } from '../src/multi-expert/orchestrator/orchestrator';
import { DiscussionTrigger } from '../src/multi-expert/triggers/trigger';
import { DecisionFormatter } from '../src/multi-expert/formatter/formatter';
import { ExpertInput } from '../src/multi-expert/experts/base-expert';

describe('Multi-Expert Orchestrator', () => {
  describe('ExpertOrchestrator', () => {
    it('should create orchestrator with default config', () => {
      const orchestrator = new ExpertOrchestrator();
      expect(orchestrator).toBeDefined();
    });

    it('should create orchestrator with custom config', () => {
      const orchestrator = new ExpertOrchestrator({
        maxRounds: 5,
        minRounds: 2,
        consensusThreshold: 0.8
      });
      expect(orchestrator).toBeDefined();
    });

    it('should orchestrate discussion and return result', async () => {
      const orchestrator = new ExpertOrchestrator({
        maxRounds: 2,
        minRounds: 1
      });
      
      const result = await orchestrator.orchestrate('test topic', {});
      
      expect(result).toHaveProperty('topic');
      expect(result).toHaveProperty('rounds');
      expect(result).toHaveProperty('consensusLevel');
      expect(result).toHaveProperty('finalDecision');
      expect(result).toHaveProperty('consensus');
      expect(result).toHaveProperty('summary');
    });

    it('should register custom expert', () => {
      const orchestrator = new ExpertOrchestrator();
      const mockExpert = {
        getProfile: () => ({
          id: 'custom',
          name: 'Custom Expert',
          role: 'Custom',
          expertise: ['custom'],
          personality: 'test'
        }),
        think: vi.fn().mockResolvedValue({
          expertId: 'custom',
          content: 'custom opinion',
          confidence: 0.8,
          concerns: [],
          metadata: {}
        })
      };
      
      orchestrator.registerExpert(mockExpert as any);
      expect(orchestrator.getExperts()).toContain(mockExpert);
    });
  });

  describe('DiscussionTrigger', () => {
    it('should create trigger with default rules', () => {
      const trigger = new DiscussionTrigger();
      expect(trigger).toBeDefined();
    });

    it('should evaluate text and return trigger result', () => {
      const trigger = new DiscussionTrigger();
      const result = trigger.evaluate('多专家讨论: 系统架构');
      
      expect(result).toHaveProperty('triggered');
      expect(result).toHaveProperty('matchedRules');
      expect(result).toHaveProperty('confidence');
    });

    it('should trigger on keyword "多专家讨论"', () => {
      const trigger = new DiscussionTrigger();
      const result = trigger.evaluate('多专家讨论这个问题');
      
      expect(result.triggered).toBe(true);
      expect(result.confidence).toBeGreaterThan(0);
    });

    it.skip('should trigger on architecture keywords', () => {
      const trigger = new DiscussionTrigger();
      const result = trigger.evaluate('我们需要设计系统架构');
      
      expect(result.triggered).toBe(true);
      expect(result.suggestedCategory).toBe('architecture-design');
    });

    it('should not trigger on normal text', () => {
      const trigger = new DiscussionTrigger();
      const result = trigger.evaluate('今天天气不错');
      
      expect(result.triggered).toBe(false);
    });

    it.skip('should add custom rule', () => {
      const trigger = new DiscussionTrigger([], 0.3); // 降低阈值
      trigger.addRule({
        id: 'custom-rule',
        name: 'Custom Rule',
        description: 'Test custom rule',
        conditions: [{ type: 'keyword', value: 'custom', operator: 'contains', weight: 1 }],
        config: { category: 'technology-selection', priority: 'medium', maxRounds: 3, requireCaptainApproval: false },
        actions: [{ type: 'discuss' }],
        enabled: true
      });
      
      const result = trigger.evaluate('this is custom');
      expect(result.triggered).toBe(true);
      expect(result.matchedRules.length).toBeGreaterThan(0);
    });
  });

  describe('DecisionFormatter', () => {
    it('should format decision to markdown', () => {
      const decision = {
        topic: 'Test Decision',
        finalDecision: {
          expertId: 'captain',
          expertName: '队长',
          opinion: 'Proceed with plan A',
          keyPoints: ['计划可行'],
          confidence: 0.85,
          concerns: [],
          metadata: {}
        },
        consensusLevel: 0.85,
        consensus: true,
        opinions: [
          { 
            expertId: 'researcher', 
            expertName: '研究员',
            opinion: 'Data supports this', 
            keyPoints: ['数据支持'],
            confidence: 0.9,
            concerns: [],
            metadata: {}
          },
          { 
            expertId: 'architect', 
            expertName: '架构师',
            opinion: 'Design is sound', 
            keyPoints: ['设计合理'],
            confidence: 0.8,
            concerns: [],
            metadata: {}
          }
        ],
        rounds: [
          {
            roundNumber: 1,
            opinions: [
              { 
                expertId: 'researcher', 
                expertName: '研究员',
                opinion: 'Data supports this', 
                keyPoints: ['数据支持'],
                confidence: 0.9,
                concerns: [],
                metadata: {}
              }
            ]
          }
        ]
      };
      
      const format = DecisionFormatter.format(decision);
      const markdown = DecisionFormatter.toMarkdown(format);
      
      expect(markdown).toContain('# MoltCare 决策报告');
      expect(markdown).toContain('Test Decision');
      expect(markdown).toContain('Proceed with plan A');
    });

    it('should format decision to JSON', () => {
      const decision = {
        topic: 'Test Decision',
        finalDecision: {
          expertId: 'captain',
          expertName: '队长',
          opinion: 'Proceed',
          keyPoints: ['继续'],
          confidence: 0.9,
          concerns: [],
          metadata: {}
        },
        consensusLevel: 0.9,
        consensus: true,
        opinions: [],
        rounds: []
      };
      
      const format = DecisionFormatter.format(decision);
      const json = DecisionFormatter.toJSON(format);
      const parsed = JSON.parse(json);
      
      expect(parsed).toHaveProperty('metadata');
      expect(parsed).toHaveProperty('executiveSummary');
      expect(parsed).toHaveProperty('analysis');
    });

    it('should format with specific template', () => {
      const decision = {
        topic: 'Technology Selection',
        finalDecision: {
          expertId: 'captain',
          expertName: '队长',
          opinion: 'Use PostgreSQL',
          keyPoints: ['使用 PostgreSQL'],
          confidence: 0.75,
          concerns: [],
          metadata: {}
        },
        consensusLevel: 0.75,
        consensus: true,
        opinions: [],
        rounds: []
      };
      
      const format = DecisionFormatter.format(decision, 'technology-selection');
      const markdown = DecisionFormatter.toMarkdown(format);
      
      expect(markdown).toContain('PostgreSQL');
    });
  });
});
