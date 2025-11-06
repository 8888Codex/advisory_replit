"""
Seed analytics data with realistic user activity for testing the Analytics Dashboard.
Generates 30 days of varied activity patterns.
"""
import asyncio
from datetime import datetime, timedelta
import random
import os
import json
import asyncpg


async def seed_analytics_data():
    """
    Populate user_activity table with realistic test data spanning 30 days.
    Creates varied patterns: weekday spikes, weekend drops, streaks, etc.
    """
    print("\n[Analytics Seed] Starting analytics data seeding...")
    
    # Connect to PostgreSQL
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("[Analytics Seed] ❌ DATABASE_URL not found - skipping seed")
        return
    
    # Get real experts from storage to use correct IDs
    from storage import storage
    all_experts = await storage.get_experts()
    if not all_experts:
        print("[Analytics Seed] ⚠️ No experts found in storage - cannot seed")
        return
    
    # Create list of (id, name) tuples for seeding
    expert_data = [(expert.id, expert.name) for expert in all_experts]
    print(f"[Analytics Seed] Found {len(expert_data)} experts in storage")
    
    conn = await asyncpg.connect(database_url)
    
    try:
        user_id = "default"
        now = datetime.utcnow()
        
        # Action types with realistic weights
        action_types = [
            ("chat_message", 0.5),      # 50% - most common
            ("council_created", 0.15),  # 15%
            ("council_message", 0.25),  # 25%
            ("expert_viewed", 0.1)      # 10%
        ]
        
        activities_created = 0
        
        # Generate 30 days of data
        for day_offset in range(30, -1, -1):
            date = now - timedelta(days=day_offset)
            
            # Realistic patterns
            is_weekend = date.weekday() >= 5
            is_recent = day_offset < 7
            
            # Activity count: fewer on weekends, more recent = higher
            if is_weekend:
                daily_actions = random.randint(1, 4)
            elif is_recent:
                daily_actions = random.randint(5, 12)
            else:
                daily_actions = random.randint(3, 8)
            
            # Skip some days randomly (simulate gaps)
            if random.random() < 0.15:  # 15% chance of no activity
                continue
            
            for _ in range(daily_actions):
                # Pick action type based on weights
                action_type = random.choices(
                    [a[0] for a in action_types],
                    weights=[a[1] for a in action_types]
                )[0]
                
                # Pick random expert (use REAL expert ID and name from storage)
                expert_id, expert_name = random.choice(expert_data)
                
                # Simulate session/conversation IDs
                session_id = f"session_{date.strftime('%Y%m%d')}_{random.randint(1000, 9999)}"
                
                # Metadata varies by action type
                metadata = {}
                if action_type == "chat_message":
                    metadata = {
                        "message_count": random.randint(3, 15),
                        "conversation_id": session_id
                    }
                elif action_type == "council_created":
                    metadata = {
                        "expert_count": random.randint(2, 5),
                        "council_id": session_id
                    }
                elif action_type == "council_message":
                    metadata = {
                        "message_count": random.randint(5, 20),
                        "council_id": session_id
                    }
                elif action_type == "expert_viewed":
                    metadata = {
                        "category": random.choice([
                            "Branding", "Copywriting", "Digital Marketing",
                            "Estratégia", "Growth", "Publicidade"
                        ])
                    }
                
                # Insert activity (using REAL expert IDs and names from storage)
                rich_metadata = {
                    "expertId": expert_id,
                    "expertName": expert_name,
                    **metadata
                }
                
                try:
                    await conn.execute(
                        """
                        INSERT INTO user_activity 
                        (user_id, activity_type, metadata, created_at)
                        VALUES ($1, $2, $3::jsonb, $4)
                        """,
                        user_id,
                        action_type,
                        json.dumps(rich_metadata),
                        date - timedelta(
                            hours=random.randint(9, 20),
                            minutes=random.randint(0, 59)
                        )
                    )
                    activities_created += 1
                except Exception as e:
                    print(f"[Analytics Seed] Error inserting activity: {e}")
                    import traceback
                    traceback.print_exc()
    
        print(f"[Analytics Seed] ✅ Created {activities_created} activity records across 30 days")
        
        # Create some favorite insights for testing highlights (using correct schema)
        try:
            # Sample favorites with proper schema
            favorites = [
                {
                    "item_type": "conversation_message",
                    "item_id": "msg_1",
                    "expert": "seth-godin",
                    "snippet": "Marketing is about making change happen. The best marketing is not about the stuff you make, but the stories you tell."
                },
                {
                    "item_type": "council_message",
                    "item_id": "msg_2",
                    "expert": "robert-cialdini",
                    "snippet": "Reciprocity is one of the most powerful principles of persuasion. When you give first, people feel obligated to give back."
                },
                {
                    "item_type": "conversation_message",
                    "item_id": "msg_3",
                    "expert": "gary-vaynerchuk",
                    "snippet": "Document, don't create. Show the behind-the-scenes of your business. Authenticity wins in the attention economy."
                }
            ]
            
            for fav in favorites:
                await conn.execute(
                    """
                    INSERT INTO user_favorites (user_id, item_type, item_id, metadata)
                    VALUES ($1, $2, $3, $4::jsonb)
                    ON CONFLICT DO NOTHING
                    """,
                    user_id,
                    fav["item_type"],
                    fav["item_id"],
                    json.dumps({"expertName": fav["expert"], "snippet": fav["snippet"]})
                )
            
            print(f"[Analytics Seed] ✅ Created sample favorite insights")
        except Exception as e:
            print(f"[Analytics Seed] Note: {e}")
        
        print("[Analytics Seed] Seeding complete! Dashboard should now show realistic data.\n")
    
    finally:
        await conn.close()


async def clear_analytics_data():
    """Clear all analytics data (for testing/reset)"""
    print("\n[Analytics Seed] Clearing analytics data...")
    
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("[Analytics Seed] ❌ DATABASE_URL not found - skipping clear")
        return
    
    conn = await asyncpg.connect(database_url)
    
    try:
        user_id = "default"
        await conn.execute("DELETE FROM user_activity WHERE user_id = $1", user_id)
        await conn.execute("DELETE FROM user_favorites WHERE user_id = $1", user_id)
        print("[Analytics Seed] ✅ Cleared analytics data\n")
    except Exception as e:
        print(f"[Analytics Seed] Error clearing data: {e}")
    finally:
        await conn.close()


if __name__ == "__main__":
    # Run seed when executed directly
    asyncio.run(seed_analytics_data())
