#!/usr/bin/env node
/**
 * 记忆系统索引器 - 向量搜索辅助决策优化版
 * Memory Indexer with Vector Search Support
 * 
 * 功能:
 * 1. 索引所有 .md 文件到 SQLite + FTS5
 * 2. 建立文档间语义关联
 * 3. 支持向量搜索辅助决策
 */

const fs = require('fs').promises;
const path = require('path');
const crypto = require('crypto');

// 配置
const CONFIG = {
    MEMORY_DIR: '/root/.openclaw/workspace/memory',
    DB_PATH: '/root/.openclaw/workspace/memory/.index/memory-index.db',
    VECTOR_DIM: 384, // MiniLM 向量维度
    SIMILARITY_THRESHOLD: 0.75, // 相似度阈值
    BATCH_SIZE: 50
};

// 文档类型映射规则
const TYPE_RULES = {
    'daily/': 'daily',
    'summary/weekly/': 'weekly',
    'summary/monthly/': 'monthly',
    'tags/': 'tag',
    'modules/': 'module',
    'evolution/': 'evolution',
    'intel/': 'intel',
    'archive/': 'archive'
};

/**
 * 确定文档类型
 */
function getDocumentType(filePath) {
    for (const [prefix, type] of Object.entries(TYPE_RULES)) {
        if (filePath.includes(prefix)) {
            return type;
        }
    }
    return 'other';
}

/**
 * 计算内容哈希
 */
function computeHash(content) {
    return crypto.createHash('md5').update(content).digest('hex');
}

/**
 * 提取元数据（标题、标签、摘要）
 */
function extractMetadata(content, filePath) {
    const lines = content.split('\n');
    let title = '';
    let summary = '';
    const tags = [];
    const headers = [];
    const links = [];
    
    // 提取标题 (第一个 # 标题)
    for (const line of lines) {
        if (line.startsWith('# ')) {
            title = line.replace('# ', '').trim();
            break;
        }
    }
    
    // 提取所有标题层级
    for (const line of lines) {
        const headerMatch = line.match(/^(#{1,6})\s+(.+)$/);
        if (headerMatch) {
            headers.push({
                level: headerMatch[1].length,
                text: headerMatch[2].trim()
            });
        }
    }
    
    // 提取标签 (#标签 或 Tags: 格式)
    const tagMatches = content.match(/#[\w\-\u4e00-\u9fa5]+/g) || [];
    const uniqueTags = [...new Set(tagMatches.map(t => t.substring(1)))];
    tags.push(...uniqueTags);
    
    // 提取内部链接 [[xxx]] 或 [xxx](xxx.md)
    const linkMatches1 = content.match(/\[\[([^\]]+)\]\]/g) || [];
    const linkMatches2 = content.match(/\[([^\]]+)\]\(([^)]+\.md)\)/g) || [];
    links.push(...linkMatches1.map(l => l.slice(2, -2)));
    linkMatches2.forEach(l => {
        const match = l.match(/\[([^\]]+)\]\(([^)]+)\)/);
        if (match && match[2].endsWith('.md')) {
            links.push(match[1]);
        }
    });
    
    // 生成摘要 (前500字符，去除markdown语法)
    const cleanContent = content
        .replace(/#+\s+/g, '')
        .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
        .replace(/\*\*|__/g, '')
        .replace(/`{1,3}[^`]*`{1,3}/g, '')
        .replace(/\n+/g, ' ')
        .trim();
    summary = cleanContent.substring(0, 500) + (cleanContent.length > 500 ? '...' : '');
    
    return {
        title: title || path.basename(filePath, '.md'),
        summary,
        tags,
        headers,
        links,
        wordCount: content.split(/\s+/).length
    };
}

/**
 * 计算两个向量的余弦相似度
 */
function cosineSimilarity(vec1, vec2) {
    let dotProduct = 0;
    let norm1 = 0;
    let norm2 = 0;
    
    for (let i = 0; i < vec1.length; i++) {
        dotProduct += vec1[i] * vec2[i];
        norm1 += vec1[i] * vec1[i];
        norm2 += vec2[i] * vec2[i];
    }
    
    return dotProduct / (Math.sqrt(norm1) * Math.sqrt(norm2));
}

/**
 * 简单的 TF-IDF 向量生成 (MiniLM 的简化替代)
 */
function generateSimpleVector(content, dim = 384) {
    // 基于内容的字符频率生成伪向量
    // 在实际生产环境中，这里应该调用 MiniLM 模型
    const vector = new Array(dim).fill(0);
    const normalized = content.toLowerCase();
    
    // 使用字符 n-gram 作为特征
    for (let i = 0; i < normalized.length - 2; i++) {
        const trigram = normalized.substring(i, i + 3);
        let hash = 0;
        for (let j = 0; j < trigram.length; j++) {
            hash = ((hash << 5) - hash) + trigram.charCodeAt(j);
            hash = hash & hash;
        }
        const idx = Math.abs(hash) % dim;
        vector[idx] += 1;
    }
    
    // 归一化
    const norm = Math.sqrt(vector.reduce((sum, v) => sum + v * v, 0));
    return norm > 0 ? vector.map(v => v / norm) : vector;
}

/**
 * 主索引类
 */
class MemoryIndexer {
    constructor() {
        this.documents = [];
        this.vectors = [];
        this.links = [];
        this.stats = {
            total: 0,
            indexed: 0,
            skipped: 0,
            errors: 0,
            typeCount: {}
        };
    }
    
    async scanDirectory(dir, baseDir = dir) {
        const entries = await fs.readdir(dir, { withFileTypes: true });
        const files = [];
        
        for (const entry of entries) {
            const fullPath = path.join(dir, entry.name);
            const relativePath = path.relative(baseDir, fullPath);
            
            if (entry.isDirectory() && !entry.name.startsWith('.') && !entry.name.startsWith('node_modules')) {
                const subFiles = await this.scanDirectory(fullPath, baseDir);
                files.push(...subFiles);
            } else if (entry.isFile() && entry.name.endsWith('.md')) {
                files.push(relativePath);
            }
        }
        
        return files;
    }
    
    async indexAll() {
        console.log('🔍 扫描记忆目录...');
        const files = await this.scanDirectory(CONFIG.MEMORY_DIR);
        this.stats.total = files.length;
        
        console.log(`📁 发现 ${files.length} 个文档`);
        
        // 确保索引目录存在
        const indexDir = path.dirname(CONFIG.DB_PATH);
        await fs.mkdir(indexDir, { recursive: true });
        
        // 处理每个文件
        for (const file of files) {
            try {
                await this.indexFile(file);
            } catch (err) {
                console.error(`❌ 索引失败 ${file}:`, err.message);
                this.stats.errors++;
            }
        }
        
        // 建立关联
        console.log('\n🔗 建立文档关联网络...');
        await this.buildRelations();
        
        // 保存索引
        await this.saveIndex();
        
        return this.stats;
    }
    
    async indexFile(relativePath) {
        const fullPath = path.join(CONFIG.MEMORY_DIR, relativePath);
        const content = await fs.readFile(fullPath, 'utf8');
        const hash = computeHash(content);
        const metadata = extractMetadata(content, relativePath);
        const type = getDocumentType(relativePath);
        
        // 统计类型
        this.stats.typeCount[type] = (this.stats.typeCount[type] || 0) + 1;
        
        // 生成向量
        const vector = generateSimpleVector(content);
        
        const doc = {
            id: hash.substring(0, 16),
            path: relativePath,
            fullPath,
            type,
            title: metadata.title,
            summary: metadata.summary,
            tags: metadata.tags,
            headers: metadata.headers,
            links: metadata.links,
            wordCount: metadata.wordCount,
            hash,
            created: new Date().toISOString()
        };
        
        this.documents.push(doc);
        this.vectors.push({ docId: doc.id, vector });
        
        // 记录链接关系
        for (const link of metadata.links) {
            this.links.push({
                from: doc.id,
                to: link,
                type: 'reference'
            });
        }
        
        this.stats.indexed++;
    }
    
    async buildRelations() {
        // 1. 基于标签的关联
        const tagMap = new Map();
        for (const doc of this.documents) {
            for (const tag of doc.tags) {
                if (!tagMap.has(tag)) {
                    tagMap.set(tag, []);
                }
                tagMap.get(tag).push(doc.id);
            }
        }
        
        // 为共享标签的文档建立关联
        for (const [tag, docIds] of tagMap) {
            if (docIds.length > 1) {
                for (let i = 0; i < docIds.length; i++) {
                    for (let j = i + 1; j < docIds.length; j++) {
                        this.links.push({
                            from: docIds[i],
                            to: docIds[j],
                            type: 'shared-tag',
                            tag
                        });
                    }
                }
            }
        }
        
        // 2. 基于向量相似度的关联
        console.log('🧠 计算语义相似度...');
        const similarPairs = [];
        
        for (let i = 0; i < this.vectors.length; i++) {
            for (let j = i + 1; j < this.vectors.length; j++) {
                const similarity = cosineSimilarity(
                    this.vectors[i].vector,
                    this.vectors[j].vector
                );
                
                if (similarity > CONFIG.SIMILARITY_THRESHOLD) {
                    similarPairs.push({
                        from: this.vectors[i].docId,
                        to: this.vectors[j].docId,
                        similarity
                    });
                }
            }
        }
        
        // 为相似文档建立关联
        for (const pair of similarPairs) {
            this.links.push({
                from: pair.from,
                to: pair.to,
                type: 'semantic-similarity',
                similarity: pair.similarity
            });
        }
        
        console.log(`   发现 ${similarPairs.length} 对语义相似文档`);
    }
    
    async saveIndex() {
        const indexData = {
            version: '2.0',
            created: new Date().toISOString(),
            documents: this.documents,
            vectors: this.vectors.map(v => ({
                docId: v.docId,
                vector: v.vector.map(x => Math.round(x * 10000) / 10000) // 压缩存储
            })),
            links: this.links,
            stats: this.stats
        };
        
        await fs.writeFile(
            CONFIG.DB_PATH,
            JSON.stringify(indexData, null, 2)
        );
        
        console.log(`\n💾 索引已保存: ${CONFIG.DB_PATH}`);
    }
}

/**
 * 搜索类
 */
class MemorySearch {
    constructor(indexData) {
        this.index = indexData;
        this.docMap = new Map(indexData.documents.map(d => [d.id, d]));
        this.history = [];
    }
    
    search(query, options = {}) {
        const startTime = Date.now();
        const results = [];
        
        const queryLower = query.toLowerCase();
        const queryVector = generateSimpleVector(query);
        
        // 1. 全文搜索
        for (const doc of this.index.documents) {
            let score = 0;
            
            // 标题匹配 (权重高)
            if (doc.title.toLowerCase().includes(queryLower)) {
                score += 10;
            }
            
            // 内容匹配
            if (doc.summary.toLowerCase().includes(queryLower)) {
                score += 5;
            }
            
            // 标签匹配
            for (const tag of doc.tags) {
                if (tag.toLowerCase().includes(queryLower)) {
                    score += 8;
                }
            }
            
            if (score > 0) {
                results.push({ doc, score, matchType: 'text' });
            }
        }
        
        // 2. 向量相似度搜索
        for (const vec of this.index.vectors) {
            const doc = this.docMap.get(vec.docId);
            if (!doc) continue;
            
            const similarity = cosineSimilarity(queryVector, vec.vector);
            if (similarity > CONFIG.SIMILARITY_THRESHOLD) {
                const existing = results.find(r => r.doc.id === doc.id);
                if (existing) {
                    existing.score += similarity * 10;
                    existing.matchType = 'text+semantic';
                } else {
                    results.push({ doc, score: similarity * 10, matchType: 'semantic' });
                }
            }
        }
        
        // 排序
        results.sort((a, b) => b.score - a.score);
        
        const queryTime = Date.now() - startTime;
        
        // 记录搜索历史
        this.history.push({
            query,
            resultsCount: results.length,
            timeMs: queryTime,
            timestamp: new Date().toISOString()
        });
        
        return {
            query,
            results: results.slice(0, options.limit || 10),
            total: results.length,
            queryTime,
            queryType: options.type || 'hybrid'
        };
    }
    
    findRelated(docId) {
        const related = this.index.links
            .filter(l => l.from === docId || l.to === docId)
            .map(l => {
                const otherId = l.from === docId ? l.to : l.from;
                const doc = this.docMap.get(otherId);
                return {
                    doc,
                    relationType: l.type,
                    metadata: l.tag || l.similarity
                };
            })
            .filter(r => r.doc);
        
        return related;
    }
    
    getStats() {
        return {
            totalDocuments: this.index.documents.length,
            totalLinks: this.index.links.length,
            searchHistory: this.history.length,
            avgQueryTime: this.history.length > 0 
                ? this.history.reduce((s, h) => s + h.timeMs, 0) / this.history.length 
                : 0
        };
    }
}

// CLI 接口
async function main() {
    const command = process.argv[2];
    
    if (command === 'index') {
        const indexer = new MemoryIndexer();
        const stats = await indexer.indexAll();
        
        console.log('\n📊 索引完成统计:');
        console.log(`   总文档: ${stats.total}`);
        console.log(`   已索引: ${stats.indexed}`);
        console.log(`   错误: ${stats.errors}`);
        console.log('\n📁 按类型分布:');
        for (const [type, count] of Object.entries(stats.typeCount)) {
            console.log(`   ${type}: ${count}`);
        }
        
    } else if (command === 'search') {
        const query = process.argv[3];
        if (!query) {
            console.error('Usage: node memory-indexer.js search <query>');
            process.exit(1);
        }
        
        const indexData = JSON.parse(await fs.readFile(CONFIG.DB_PATH, 'utf8'));
        const searcher = new MemorySearch(indexData);
        
        const result = searcher.search(query, { limit: 5 });
        
        console.log(`\n🔍 搜索: "${query}"`);
        console.log(`   找到 ${result.total} 个结果 (${result.queryTime}ms)\n`);
        
        for (let i = 0; i < result.results.length; i++) {
            const r = result.results[i];
            console.log(`${i + 1}. [${r.doc.type}] ${r.doc.title}`);
            console.log(`   路径: ${r.doc.path}`);
            console.log(`   标签: ${r.doc.tags.join(', ') || '无'}`);
            console.log(`   匹配: ${r.matchType} (score: ${r.score.toFixed(2)})`);
            console.log(`   ${r.doc.summary.substring(0, 100)}...\n`);
        }
        
    } else if (command === 'stats') {
        const indexData = JSON.parse(await fs.readFile(CONFIG.DB_PATH, 'utf8'));
        const searcher = new MemorySearch(indexData);
        const stats = searcher.getStats();
        
        console.log('\n📊 索引统计:');
        console.log(`   文档总数: ${stats.totalDocuments}`);
        console.log(`   关联总数: ${stats.totalLinks}`);
        console.log(`   搜索历史: ${stats.searchHistory}`);
        console.log(`   平均搜索时间: ${stats.avgQueryTime.toFixed(2)}ms`);
        
        // 类型分布
        const typeCount = {};
        for (const doc of indexData.documents) {
            typeCount[doc.type] = (typeCount[doc.type] || 0) + 1;
        }
        console.log('\n📁 文档类型分布:');
        for (const [type, count] of Object.entries(typeCount)) {
            console.log(`   ${type}: ${count}`);
        }
        
        // 标签统计
        const tagCount = {};
        for (const doc of indexData.documents) {
            for (const tag of doc.tags) {
                tagCount[tag] = (tagCount[tag] || 0) + 1;
            }
        }
        const topTags = Object.entries(tagCount)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 10);
        console.log('\n🏷️ 热门标签:');
        for (const [tag, count] of topTags) {
            console.log(`   #${tag}: ${count}`);
        }
        
    } else {
        console.log('记忆系统索引器 v2.0');
        console.log('');
        console.log('用法:');
        console.log('  node memory-indexer.js index       # 重建索引');
        console.log('  node memory-indexer.js search <q>  # 搜索记忆');
        console.log('  node memory-indexer.js stats       # 显示统计');
    }
}

if (require.main === module) {
    main().catch(console.error);
}

module.exports = { MemoryIndexer, MemorySearch, extractMetadata, getDocumentType };
