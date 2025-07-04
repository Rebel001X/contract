# from llama_index.core import SimpleDirectoryReader
# # from llama_index.vector_stores.milvus import MilvusVectorStore  # 删除这行
# from llama_index.core import VectorStoreIndex
# # from llama_index.embeddings.openai import OpenAIEmbedding  # 删除这行
# from llama_index.core.node_parser import SimpleNodeParser
# from llama_index.core.extractors import SummaryExtractor, KeywordExtractor
# from llama_index.vectorstores.milvus import MilvusVectorStore
#
# class MilvusRAG:
#     def __init__(self, docs_path: str, milvus_uri: str, collection_name: str = "rag_collection"):
#         self.docs_path = docs_path
#         self.milvus_uri = milvus_uri
#         self.collection_name = collection_name
#         self.index = None
#         self.documents = None
#
#     def build_index(self):
#         # 加载文档
#         self.documents = SimpleDirectoryReader(self.docs_path).load_data()
#         # 配置Milvus向量存储
#         vector_store = MilvusVectorStore(
#             uri=self.milvus_uri,
#             collection_name=self.collection_name
#         )
#         # 构建向量索引并存储到Milvus
#         self.index = VectorStoreIndex.from_documents(
#             self.documents,
#             vector_store=vector_store,
#         )
#
#     def query(self, question: str):
#         if not self.index:
#             raise ValueError("Index not built. Call build_index() first.")
#         query_engine = self.index.as_query_engine()
#         return query_engine.query(question)
#
#     def summary(self):
#         """对所有文档做摘要"""
#         if not self.documents:
#             raise ValueError("No documents loaded. Call build_index() first.")
#         parser = SimpleNodeParser()
#         nodes = parser.get_nodes_from_documents(self.documents)
#         extractor = SummaryExtractor()
#         summaries = [extractor.extract(node) for node in nodes]
#         return summaries
#
#     def extraction(self):
#         """对所有文档做关键信息抽取（如关键词）"""
#         if not self.documents:
#             raise ValueError("No documents loaded. Call build_index() first.")
#         parser = SimpleNodeParser()
#         nodes = parser.get_nodes_from_documents(self.documents)
#         extractor = KeywordExtractor()
#         keywords = [extractor.extract(node) for node in nodes]
#         return keywords
#
# # 使用示例：
# # rag = MilvusRAG(docs_path="./docs", milvus_uri="http://localhost:19530")
# # rag.build_index()
# # print(rag.summary())
# # print(rag.extraction())
# # answer = rag.query("你的问题是什么？")
# # print(answer)