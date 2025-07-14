"""
Gaming commands for the Rosethorn Discord Bot.
"""
import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio
from utils import create_embed, roll_dice, magic_8ball

class Games(commands.Cog):
    """Cog for interactive gaming commands."""
    
    def __init__(self, bot):
        self.bot = bot
        self.active_games = {}

    @app_commands.command(name="dice", description="Roll one or more dice")
    @app_commands.describe(
        sides="Number of sides on the dice (2-100)",
        count="Number of dice to roll (1-10)"
    )
    async def dice_roll(self, interaction: discord.Interaction, sides: int = 6, count: int = 1):
        """Roll dice command."""
        try:
            results = roll_dice(sides, count)
            total = sum(results)
            
            if count == 1:
                embed = create_embed(
                    f"🎲 Dice Roll (d{sides})",
                    f"**Result:** {results[0]}",
                    discord.Color.blue()
                )
            else:
                dice_display = " + ".join(map(str, results))
                embed = create_embed(
                    f"🎲 Dice Roll ({count}d{sides})",
                    f"**Results:** {dice_display}\n**Total:** {total}",
                    discord.Color.blue()
                )
            
            embed.set_footer(text=f"Rolled by {interaction.user.display_name}")
            await interaction.response.send_message(embed=embed)
            
        except ValueError as e:
            embed = create_embed(
                "Invalid Parameters",
                str(e),
                discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="coinflip", description="Flip a coin")
    async def coin_flip(self, interaction: discord.Interaction):
        """Flip a coin command."""
        result = random.choice(["Heads", "Tails"])
        emoji = "🪙"
        
        embed = create_embed(
            f"{emoji} Coin Flip",
            f"**Result:** {result}",
            discord.Color.gold()
        )
        embed.set_footer(text=f"Flipped by {interaction.user.display_name}")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="8ball", description="Ask the magic 8-ball a question")
    @app_commands.describe(question="Your question for the magic 8-ball")
    async def eight_ball(self, interaction: discord.Interaction, question: str):
        """Magic 8-ball command."""
        response = magic_8ball()
        
        embed = create_embed(
            "🎱 Magic 8-Ball",
            f"**Question:** {question}\n**Answer:** {response}",
            discord.Color.purple()
        )
        embed.set_footer(text=f"Asked by {interaction.user.display_name}")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="rps", description="Play Rock Paper Scissors")
    @app_commands.describe(choice="Your choice: rock, paper, or scissors")
    @app_commands.choices(choice=[
        app_commands.Choice(name="Rock", value="rock"),
        app_commands.Choice(name="Paper", value="paper"),
        app_commands.Choice(name="Scissors", value="scissors")
    ])
    async def rock_paper_scissors(self, interaction: discord.Interaction, choice: str):
        """Rock Paper Scissors game."""
        choices = ["rock", "paper", "scissors"]
        bot_choice = random.choice(choices)
        
        emojis = {
            "rock": "🪨",
            "paper": "📄", 
            "scissors": "✂️"
        }
        
        # Determine winner
        if choice == bot_choice:
            result = "It's a tie!"
            color = discord.Color.yellow()
        elif (choice == "rock" and bot_choice == "scissors") or \
             (choice == "paper" and bot_choice == "rock") or \
             (choice == "scissors" and bot_choice == "paper"):
            result = "You win!"
            color = discord.Color.green()
        else:
            result = "I win!"
            color = discord.Color.red()
        
        embed = create_embed(
            "🎮 Rock Paper Scissors",
            f"**You chose:** {emojis[choice]} {choice.title()}\n" +
            f"**I chose:** {emojis[bot_choice]} {bot_choice.title()}\n\n" +
            f"**Result:** {result}",
            color
        )
        embed.set_footer(text=f"Played by {interaction.user.display_name}")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="trivia", description="Start a trivia question")
    async def trivia(self, interaction: discord.Interaction):
        """Start a trivia game."""
        # Simple trivia questions - in a real bot, you might use an API
        trivia_questions = [
            {
                "question": "What is the highest selling video game of all time?",
                "options": ["Minecraft", "Tetris", "Grand Theft Auto V", "Wii Sports"],
                "answer": 0,
                "explanation": "Minecraft has sold over 300 million copies worldwide!"
            },
            {
                "question": "Which company created the Zelda franchise?",
                "options": ["Sony", "Microsoft", "Nintendo", "Sega"],
                "answer": 2,
                "explanation": "Nintendo created The Legend of Zelda series in 1986."
            },
            {
                "question": "What year was the first PlayStation console released?",
                "options": ["1993", "1994", "1995", "1996"],
                "answer": 2,
                "explanation": "The original PlayStation was released in 1995."
            },
            {
                "question": "Which game introduced the Battle Royale genre to mainstream gaming?",
                "options": ["PUBG", "Fortnite", "Apex Legends", "H1Z1"],
                "answer": 0,
                "explanation": "PlayerUnknown's Battlegrounds (PUBG) popularized the Battle Royale genre."
            }
        ]
        
        question_data = random.choice(trivia_questions)
        
        options_text = "\n".join([f"{i+1}. {option}" for i, option in enumerate(question_data["options"])])
        
        embed = create_embed(
            "🧠 Gaming Trivia",
            f"**Question:** {question_data['question']}\n\n{options_text}\n\n" +
            "React with 1️⃣, 2️⃣, 3️⃣, or 4️⃣ to answer!",
            discord.Color.orange()
        )
        
        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()
        
        # Add reaction options
        reactions = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]
        for reaction in reactions:
            await message.add_reaction(reaction)
        
        # Store the game data
        self.active_games[message.id] = {
            "question_data": question_data,
            "participants": set(),
            "correct_users": set()
        }
        
        # Wait for reactions and then show answer
        await asyncio.sleep(30)  # Wait 30 seconds for answers
        await self._reveal_trivia_answer(message, question_data)

    async def _reveal_trivia_answer(self, message, question_data):
        """Reveal the answer to a trivia question."""
        correct_answer = question_data["options"][question_data["answer"]]
        
        embed = create_embed(
            "🧠 Trivia Answer",
            f"**Question:** {question_data['question']}\n\n" +
            f"**Correct Answer:** {question_data['answer'] + 1}. {correct_answer}\n\n" +
            f"**Explanation:** {question_data['explanation']}",
            discord.Color.green()
        )
        
        try:
            await message.edit(embed=embed)
            # Clean up the game data
            if message.id in self.active_games:
                del self.active_games[message.id]
        except:
            pass

    @app_commands.command(name="numberguess", description="Start a number guessing game")
    @app_commands.describe(max_number="Maximum number to guess (default: 100)")
    async def number_guess(self, interaction: discord.Interaction, max_number: int = 100):
        """Start a number guessing game."""
        if max_number < 10 or max_number > 1000:
            embed = create_embed(
                "Invalid Range",
                "Maximum number must be between 10 and 1000.",
                discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        secret_number = random.randint(1, max_number)
        
        embed = create_embed(
            "🔢 Number Guessing Game",
            f"I'm thinking of a number between 1 and {max_number}!\n" +
            f"You have 10 attempts to guess it. Use `/guess <number>` to make a guess.",
            discord.Color.blue()
        )
        
        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()
        
        # Store the game data
        self.active_games[f"guess_{interaction.user.id}"] = {
            "secret_number": secret_number,
            "max_number": max_number,
            "attempts": 0,
            "max_attempts": 10,
            "channel": interaction.channel,
            "user": interaction.user
        }

    @app_commands.command(name="guess", description="Make a guess in the number guessing game")
    @app_commands.describe(number="Your guess")
    async def make_guess(self, interaction: discord.Interaction, number: int):
        """Make a guess in the number guessing game."""
        game_key = f"guess_{interaction.user.id}"
        
        if game_key not in self.active_games:
            embed = create_embed(
                "No Active Game",
                "You don't have an active number guessing game. Start one with `/numberguess`!",
                discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        game_data = self.active_games[game_key]
        game_data["attempts"] += 1
        
        secret_number = game_data["secret_number"]
        attempts_left = game_data["max_attempts"] - game_data["attempts"]
        
        if number == secret_number:
            embed = create_embed(
                "🎉 Congratulations!",
                f"You guessed it! The number was **{secret_number}**.\n" +
                f"It took you {game_data['attempts']} attempts.",
                discord.Color.green()
            )
            del self.active_games[game_key]
        elif game_data["attempts"] >= game_data["max_attempts"]:
            embed = create_embed(
                "😔 Game Over",
                f"You've run out of attempts! The number was **{secret_number}**.",
                discord.Color.red()
            )
            del self.active_games[game_key]
        elif number < secret_number:
            embed = create_embed(
                "📈 Too Low!",
                f"Your guess of **{number}** is too low.\n" +
                f"Attempts remaining: {attempts_left}",
                discord.Color.yellow()
            )
        else:
            embed = create_embed(
                "📉 Too High!",
                f"Your guess of **{number}** is too high.\n" +
                f"Attempts remaining: {attempts_left}",
                discord.Color.yellow()
            )
        
        await interaction.response.send_message(embed=embed)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        """Handle trivia reactions."""
        if user.bot:
            return
            
        message = reaction.message
        if message.id not in self.active_games:
            return
            
        game_data = self.active_games[message.id]
        if "question_data" not in game_data:
            return
            
        # Map reactions to answers
        reaction_map = {"1️⃣": 0, "2️⃣": 1, "3️⃣": 2, "4️⃣": 3}
        
        if str(reaction.emoji) in reaction_map:
            user_answer = reaction_map[str(reaction.emoji)]
            correct_answer = game_data["question_data"]["answer"]
            
            if user.id not in game_data["participants"]:
                game_data["participants"].add(user.id)
                
                if user_answer == correct_answer:
                    game_data["correct_users"].add(user.id)

async def setup(bot):
    """Setup function for the cog."""
    await bot.add_cog(Games(bot))