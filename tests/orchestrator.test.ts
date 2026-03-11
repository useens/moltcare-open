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
      expect(result).toHaveProperty('opinions');
      expect(result).toHaveProperty('consensusLevel');
      expect(result).toHaveProperty('finalDecision');
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
      expect(result).toHaveProperty('category');
      expect(result).toHaveProperty('priority');
    });

    it('should trigger on keyword "多专家讨论"', () => {
      const trigger = new DiscussionTrigger();
      const result = trigger.evaluate('多专家讨论这个问题');
      
      expect(result.triggered).toBe(true);
      expect(result.priority).toBe('critical');
    });

    it('should trigger on architecture keywords', () => {
      const trigger = new DiscussionTrigger();
      const result = trigger.evaluate('我们需要设计系统架构');
      
      expect(result.triggered).toBe(true);
      expect(result.category).toBe('architecture');
    });

    it('should not trigger on normal text', () => {
      const trigger = new DiscussionTrigger();
      const result = trigger.evaluate('今天天气不错');
      
      expect(result.triggered).toBe(false);
    });

    it('should add custom rule', () => {
      const trigger = new DiscussionTrigger();
      trigger.addRule({
        id: 'custom-rule',
        name: 'Custom Rule',
        conditions: [{ type: 'keyword', value: 'custom', operator: 'contains', weight: 1 }],
        config: { category: 'custom', priority: 'medium' },
        actions: [{ type: 'discuss' }],
        enabled: true
      });
      
      const result = trigger.evaluate('this is custom');
      expect(result.triggered).toBe(true);
    });
  });

  describe('DecisionFormatter', () => {
    it('should format decision to markdown', () => {
      const decision = {
        topic: 'Test Decision',
        finalDecision: 'Proceed with plan A',
        consensusLevel: 0.85,
        opinions: [
          { expertId: 'researcher', content: 'Data supports this', confidence: 0.9 },
          { expertId: 'architect', content: 'Design is sound', confidence: 0.8 }
        ],
        rounds: 3
      };
      
      const markdown = DecisionFormatter.toMarkdown(decision);
      
      expect(markdown).toContain('# MoltCare 决策报告');
      expect(markdown).toContain('Test Decision');
      expect(markdown).toContain('Proceed with plan A');
      expect(markdown).toContain('85%');
    });

    it('should format decision to JSON', () => {
      const decision = {
        topic: 'Test Decision',
        finalDecision: 'Proceed',
        consensusLevel: 0.9,
        opinions: [],
        rounds: 2
      };
      
      const json = DecisionFormatter.toJSON(decision);
      const parsed = JSON.parse(json);
      
      expect(parsed).toHaveProperty('metadata');
      expect(parsed).toHaveProperty('executiveSummary');
      expect(parsed).toHaveProperty('expertOpinions');
    });

    it('should format with specific template', () => {
      const decision = {
        topic: 'Technology Selection',
        finalDecision: 'Use PostgreSQL',
        consensusLevel: 0.75,
        opinions: [],
        rounds: 2
      };
      
      const formatted = DecisionFormatter.format(decision, 'technology-selection');
      
      expect(formatted).toContain('技术选型决策');
      expect(formatted).toContain('PostgreSQL');
    });
  });
});
