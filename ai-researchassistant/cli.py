"""
Interactive CLI for the Personal Intelligence System.
Allows direct terminal interaction for ingesting facts, chatting, and listing memories.
"""
import sys
import os
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import rich
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt
from rich.panel import Panel

from app.storage.db import SessionLocal, init_db
from app.models.database import MemoryModel
from app.models.schemas import MemoryCategory, VerificationStatus
from app.api.endpoints.ingestion import ingest_text, TextInput
from app.services.retriever import hybrid_retriever
from app.services.grounding import grounding_service

console = Console()


def init_system():
    init_db()


def show_memories():
    db = SessionLocal()
    try:
        memories = db.query(MemoryModel).filter(MemoryModel.is_current == True).order_by(MemoryModel.category).all()
        table = Table(title="Active Personal Memories", show_header=True, header_style="bold magenta")
        table.add_column("Category", style="cyan", width=18)
        table.add_column("Status", style="green", width=16)
        table.add_column("Confidence", justify="right", width=10)
        table.add_column("Content", style="white")

        for m in memories:
            table.add_row(
                m.category.value,
                m.verification_status.value,
                f"{m.confidence_score:.2f}",
                m.content[:100] + ("..." if len(m.content) > 100 else "")
            )
        console.print(table)
    finally:
        db.close()


def ingest_flow():
    console.print(Panel("Direct Memory Ingestion", style="bold cyan"))
    title = Prompt.ask("Note / Document Title", default="Personal Profile Note")
    content = Prompt.ask("Enter the knowledge / facts about yourself")
    if not content.strip():
        console.print("[red]Content cannot be empty.[/red]")
        return

    db = SessionLocal()
    try:
        summary = ingest_text(
            data=TextInput(
                title=title,
                content=content,
                default_verification_status=VerificationStatus.VERIFIED_FACT
            ),
            db=db
        )
        console.print(f"[green]Successfully extracted {summary.memories_extracted} memories (conflicts resolved: {summary.conflicts_or_updates})[/green]")
        for m in summary.memories:
            console.print(f"  • [{m.category.value}] {m.content}")
    finally:
        db.close()


def query_flow():
    console.print(Panel("Grounded Intelligence Query", style="bold green"))
    query = Prompt.ask("Ask anything about your goals, projects, preferences, or background")
    if not query.strip():
        return

    db = SessionLocal()
    try:
        citations = hybrid_retriever.retrieve(query=query, db=db, limit=5)
        response = grounding_service.answer_query(query=query, citations=citations)

        console.print(Panel(response.answer, title=f"Grounded Response ({response.model_used})", style="bold white"))

        if response.citations:
            console.print("\n[bold underline]Supporting Memory Citations:[/bold underline]")
            for c in response.citations:
                console.print(f"  • [cyan][{c.category.value}][/cyan] [dim]{c.memory_id}[/dim] (score: {c.relevance_score}): {c.content_snippet}")
        
        if response.inferred_recommendations:
            console.print("\n[bold yellow]Inferred Recommendations:[/bold yellow]")
            for inf in response.inferred_recommendations:
                console.print(f"  ⚡ {inf}")
    finally:
        db.close()


def main():
    init_system()
    while True:
        console.print("\n[bold blue]=== Personal Intelligence System Menu ===[/bold blue]")
        console.print("1. Ingest Knowledge / Facts / Bio")
        console.print("2. Ask Grounded Question")
        console.print("3. List Stored Memories")
        console.print("4. Exit")
        choice = Prompt.ask("Select an option", choices=["1", "2", "3", "4"], default="2")

        if choice == "1":
            ingest_flow()
        elif choice == "2":
            query_flow()
        elif choice == "3":
            show_memories()
        elif choice == "4":
            console.print("[yellow]Exiting. Have a great day![/yellow]")
            break


if __name__ == "__main__":
    main()
