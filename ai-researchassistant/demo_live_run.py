"""
End-to-end live demonstration of the Personal Intelligence System.
Demonstrates:
1. Ingestion of raw personal profile notes.
2. Atomic memory extraction and classification into categories.
3. Dual persistence (Relational SQLite/PostgreSQL + Qdrant Vector Store).
4. Grounded intelligence query with Ollama and explicit memory citations.
5. Anti-hallucination rejection on ungrounded/unknown questions.
"""
import sys
import os

# Fix Windows console UTF-8 encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from app.storage.db import SessionLocal, init_db
from app.models.database import MemoryModel, MemoryAuditLogModel
from app.models.schemas import VerificationStatus, SourceType
from app.api.endpoints.ingestion import ingest_text, TextInput
from app.services.retriever import hybrid_retriever
from app.services.grounding import grounding_service

console = Console()

def run_live_demonstration():
    console.print(Panel.fit("[bold green]Personal Intelligence System - Live Execution Demo[/bold green]", style="bold cyan"))
    
    # Step 1: Initialize Database
    console.print("\n[bold yellow]Step 1: Initializing Relational & Vector Storage Layer...[/bold yellow]")
    init_db()
    console.print("[green][OK] Database schemas and Qdrant collections verified.[/green]")

    # Step 2: Ingest Sample Knowledge
    console.print("\n[bold yellow]Step 2: Ingesting Raw Personal Knowledge & Goals...[/bold yellow]")
    sample_text = (
        "My name is Basant. I am an AI systems engineer specializing in personalized cognitive memory, "
        "production RAG pipelines, and agentic reasoning architectures.\n\n"
        "My primary career goal for 2026 is to build and deploy an autonomous personal intelligence assistant "
        "that acts as my external cognitive memory and career strategist.\n\n"
        "I am currently building pythonAi, an intelligence project using Python, FastAPI, PostgreSQL, Qdrant, and Ollama. "
        "I prefer concise, evidence-grounded technical communication over generic explanations."
    )

    console.print(Panel(sample_text, title="Input Raw Text", style="dim"))

    db = SessionLocal()
    try:
        summary = ingest_text(
            data=TextInput(
                title="Basant 2026 Profile & Career Manifesto",
                content=sample_text,
                source_type=SourceType.MANUAL_ENTRY,
                default_verification_status=VerificationStatus.VERIFIED_FACT
            ),
            db=db
        )

        console.print(f"[bold green][OK] Successfully extracted {summary.memories_extracted} atomic memories![/bold green]")
        
        # Display Extracted Memories
        table = Table(title="Extracted & Indexed Memories", header_style="bold magenta")
        table.add_column("Memory ID", style="dim", width=12)
        table.add_column("Category", style="cyan", width=20)
        table.add_column("Status", style="green", width=16)
        table.add_column("Content Preview", style="white")

        for m in summary.memories:
            table.add_row(
                str(m.id)[:8] + "...",
                m.category.value,
                m.verification_status.value,
                m.content
            )
        console.print(table)

        # Step 3: Test Grounded Query
        console.print("\n[bold yellow]Step 3: Running Grounded Query against Personal Memory...[/bold yellow]")
        query1 = "What is Basant's primary goal for 2026, and what project is he building?"
        console.print(f"[bold white]Query: [/bold white]\"{query1}\"")

        citations1 = hybrid_retriever.retrieve(query=query1, db=db, limit=5)
        response1 = grounding_service.answer_query(query=query1, citations=citations1)

        console.print(Panel(
            response1.answer,
            title=f"Grounded Response (Model: {response1.model_used})",
            style="bold green"
        ))

        if response1.citations:
            console.print("[cyan]Supporting Memory Citations Grounding This Response:[/cyan]")
            for c in response1.citations:
                console.print(f"  * [bold][{c.category.value}][/bold] (Score: {c.relevance_score:.3f}): {c.content_snippet}")

        # Step 4: Test Anti-Hallucination Guard on Unknown Query
        console.print("\n[bold yellow]Step 4: Testing Anti-Hallucination Guard on Unverified/Unknown Question...[/bold yellow]")
        query2 = "What did Basant have for breakfast on March 14, 2021, and what is his favorite Martian dessert?"
        console.print(f"[bold white]Query: [/bold white]\"{query2}\"")

        citations2 = hybrid_retriever.retrieve(query=query2, db=db, limit=5, min_relevance=0.60)
        response2 = grounding_service.answer_query(query=query2, citations=citations2)

        console.print(Panel(
            response2.answer,
            title="Anti-Hallucination Refusal",
            style="bold yellow"
        ))
        console.print(f"[dim]Grounded Status: {response2.grounded} | Citations: {len(response2.citations)}[/dim]")

        # Step 5: Check Audit Trail
        console.print("\n[bold yellow]Step 5: Verifying Immutable Audit Ledger...[/bold yellow]")
        audits = db.query(MemoryAuditLogModel).order_by(MemoryAuditLogModel.created_at.desc()).limit(5).all()
        console.print(f"[green][OK] Audit ledger contains {len(audits)} logged transactions.[/green]")
        for a in audits:
            console.print(f"  * Action: [bold cyan]{a.action}[/bold cyan] | Memory: [dim]{a.memory_id[:8]}...[/dim] | Reason: {a.reason}")

    finally:
        db.close()

    console.print("\n[bold green][OK] Live demonstration completed successfully![/bold green]\n")

if __name__ == "__main__":
    run_live_demonstration()
