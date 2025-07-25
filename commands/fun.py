import discord
from discord.ext import commands
import random
import asyncio
from datetime import datetime
import config

class FunCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.gothic_quotes = [
            "In the depths of winter, I finally learned that within me there lay an invincible summer.",
            "We are all in the gutter, but some of us are looking at the stars.",
            "The only way to get rid of a temptation is to yield to it.",
            "I can resist everything except temptation.",
            "We are each our own devil, and we make this world our hell.",
            "The heart was made to be broken.",
            "Every saint has a past, and every sinner has a future.",
            "Behind every exquisite thing that existed, there was something tragic."
        ]
        
        self.gothic_jokes = [
            "Why don't vampires go to barbecues? They don't like steak.",
            "What's a ghost's favorite type of music? Soul music, naturally.",
            "Why did the skeleton go to the party alone? He had no body to go with.",
            "What do you call a vampire who's a neat freak? Count Spatula.",
            "Why don't mummies take vacations? They're afraid they'll relax and unwind.",
            "What's a witch's favorite subject in school? Spelling, obviously.",
            "Why did the zombie break up with his girlfriend? She wasn't his type."
        ]
    
    @commands.command(name='quote')
    async def gothic_quote(self, ctx):
        """Get an inspirational Gothic quote"""
        quote = random.choice(self.gothic_quotes)
        
        embed = await self.bot.create_embed(
            "🌹 Gothic Wisdom",
            f"*\"{quote}\"*"
        )
        embed.set_footer(text="💭 Wisdom from the shadows of our Victorian manor")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='joke')
    async def gothic_joke(self, ctx):
        """Tell a Gothic-themed joke"""
        joke = random.choice(self.gothic_jokes)
        
        embed = await self.bot.create_embed(
            "😈 Gothic Humor",
            joke
        )
        embed.set_footer(text="🎭 Even in darkness, we find reason to smile")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='8ball')
    async def magic_8ball(self, ctx, *, question=None):
        """Ask the Gothic crystal ball"""
        if not question:
            embed = await self.bot.create_embed(
                "Crystal Ball Awaits",
                "Ask thy question to the mystical Gothic oracle..."
            )
            embed.add_field(
                name="Usage",
                value=f"`{ctx.prefix}8ball <your question>`",
                inline=False
            )
            await ctx.send(embed=embed)
            return
        
        responses = [
            "The shadows whisper... yes.",
            "The candlelight flickers... no.",
            "The Gothic spirits are uncertain.",
            "Thy destiny is written in darkness... yes.",
            "The manor's ancient walls say no.",
            "The ravens bring news of certainty.",
            "The mists of time obscure the answer.",
            "Victorian wisdom suggests yes.",
            "The Gothic oracle sees darkness ahead.",
            "Thy question pierces the veil... yes.",
            "The thorns of fate say no.",
            "Ask again when the moon is full.",
            "The portraits in the gallery nod yes.",
            "The basement crypts echo with no.",
            "Thy answer lies in the rose garden."
        ]
        
        response = random.choice(responses)
        
        embed = await self.bot.create_embed(
            "🔮 Gothic Oracle Speaks",
            f"**Question:** {question}\n\n**Answer:** {response}"
        )
        embed.set_footer(text="🌙 The mystical powers of our Victorian manor")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='dice', aliases=['roll'])
    async def roll_dice(self, ctx, dice: str = "1d6"):
        """Roll Gothic dice"""
        try:
            # Parse dice notation (e.g., 2d6, 1d20)
            if 'd' not in dice:
                dice = f"1d{dice}"
            
            num_dice, num_sides = dice.lower().split('d')
            num_dice = int(num_dice) if num_dice else 1
            num_sides = int(num_sides)
            
            if num_dice > 10 or num_sides > 100:
                embed = await self.bot.create_embed(
                    "Dice Limitation",
                    "The Gothic dice are limited to 10 dice with 100 sides each."
                )
                await ctx.send(embed=embed, delete_after=10)
                return
            
            rolls = [random.randint(1, num_sides) for _ in range(num_dice)]
            total = sum(rolls)
            
            embed = await self.bot.create_embed(
                "🎲 Gothic Dice Roll",
                f"Rolling {num_dice}d{num_sides} in the candlelit manor..."
            )
            embed.add_field(
                name="Rolls",
                value=" + ".join(map(str, rolls)) if len(rolls) <= 10 else f"{len(rolls)} rolls",
                inline=True
            )
            embed.add_field(
                name="Total",
                value=str(total),
                inline=True
            )
            
            # Add flavor based on result
            if total == num_dice:
                embed.add_field(
                    name="🔥 Result",
                    value="The shadows curse thy roll!",
                    inline=False
                )
            elif total == num_dice * num_sides:
                embed.add_field(
                    name="✨ Result",
                    value="The Gothic gods smile upon thee!",
                    inline=False
                )
            
            await ctx.send(embed=embed)
            
        except ValueError:
            embed = await self.bot.create_embed(
                "Invalid Dice",
                "Please use proper dice notation (e.g., 2d6, 1d20)"
            )
            await ctx.send(embed=embed, delete_after=10)
    
    @commands.command(name='choose')
    async def choose_option(self, ctx, *, options=None):
        """Let the Gothic manor choose for you"""
        if not options:
            embed = await self.bot.create_embed(
                "Gothic Choice Maker",
                "Let the wisdom of the Victorian manor guide thy decision..."
            )
            embed.add_field(
                name="Usage",
                value=f"`{ctx.prefix}choose option1, option2, option3`",
                inline=False
            )
            await ctx.send(embed=embed)
            return
        
        choices = [choice.strip() for choice in options.split(',')]
        
        if len(choices) < 2:
            embed = await self.bot.create_embed(
                "Not Enough Options",
                "Thou must provide at least two choices for the Gothic oracle."
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        chosen = random.choice(choices)
        
        embed = await self.bot.create_embed(
            "🌹 Gothic Decision",
            f"After consulting the ancient wisdom of the manor..."
        )
        embed.add_field(
            name="The Manor Chooses",
            value=f"**{chosen}**",
            inline=False
        )
        embed.add_field(
            name="All Options",
            value=", ".join(choices),
            inline=False
        )
        embed.set_footer(text="🕯️ Trust in the Gothic wisdom")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='trivia')
    async def gothic_trivia(self, ctx):
        """Gothic trivia game"""
        questions = [
            {
                "question": "What is the most famous Gothic novel written by Bram Stoker?",
                "options": ["Dracula", "Frankenstein", "The Castle of Otranto", "The Vampire"],
                "answer": 0
            },
            {
                "question": "Which architectural feature is characteristic of Gothic style?",
                "options": ["Round arches", "Flying buttresses", "Doric columns", "Flat roofs"],
                "answer": 1
            },
            {
                "question": "In what century did the Gothic Revival movement begin?",
                "options": ["16th century", "17th century", "18th century", "19th century"],
                "answer": 2
            },
            {
                "question": "Who wrote 'The Strange Case of Dr. Jekyll and Mr. Hyde'?",
                "options": ["Oscar Wilde", "Robert Louis Stevenson", "Edgar Allan Poe", "Mary Shelley"],
                "answer": 1
            },
            {
                "question": "What flower is most associated with Gothic Romance?",
                "options": ["Rose", "Lily", "Violet", "Carnation"],
                "answer": 0
            }
        ]
        
        question_data = random.choice(questions)
        
        embed = await self.bot.create_embed(
            "🎓 Gothic Trivia Challenge",
            question_data["question"]
        )
        
        option_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]
        for i, option in enumerate(question_data["options"]):
            embed.add_field(
                name=f"{option_emojis[i]} Option {i+1}",
                value=option,
                inline=True
            )
        
        embed.set_footer(text="React with the number of thy answer! ⏰ 30 seconds")
        
        message = await ctx.send(embed=embed)
        
        # Add reactions
        for i in range(len(question_data["options"])):
            await message.add_reaction(option_emojis[i])
        
        def check(reaction, user):
            return (user == ctx.author and 
                   str(reaction.emoji) in option_emojis[:len(question_data["options"])] and
                   reaction.message.id == message.id)
        
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
            
            selected = option_emojis.index(str(reaction.emoji))
            correct = question_data["answer"]
            
            if selected == correct:
                result_embed = await self.bot.create_embed(
                    "🎉 Correct!",
                    f"Thou hast chosen wisely! The answer was indeed **{question_data['options'][correct]}**."
                )
                result_embed.color = 0x00FF00
                
                # Award currency
                await self.bot.economy_service.add_currency(ctx.author.id, 50, "Trivia correct answer")
                result_embed.add_field(
                    name="Reward",
                    value="🌹 50 Gothic currency awarded!",
                    inline=False
                )
            else:
                result_embed = await self.bot.create_embed(
                    "❌ Incorrect",
                    f"Alas, the shadows deceived thee. The correct answer was **{question_data['options'][correct]}**."
                )
                result_embed.color = 0xFF0000
                
                # Consolation prize
                await self.bot.economy_service.add_currency(ctx.author.id, 10, "Trivia participation")
                result_embed.add_field(
                    name="Consolation",
                    value="🌹 10 Gothic currency for thy attempt!",
                    inline=False
                )
            
            await ctx.send(embed=result_embed)
            
        except asyncio.TimeoutError:
            timeout_embed = await self.bot.create_embed(
                "⏰ Time's Up",
                f"The Gothic clock strikes! The answer was **{question_data['options'][question_data['answer']]}**."
            )
            await ctx.send(embed=timeout_embed)
    
    @commands.command(name='aesthetic')
    async def generate_aesthetic(self, ctx):
        """Generate a Gothic aesthetic description"""
        adjectives = ["mysterious", "elegant", "haunting", "ethereal", "melancholic", "dramatic", "romantic", "dark"]
        nouns = ["moonlight", "candleflame", "rose petals", "velvet curtains", "ancient books", "crystal goblets", "marble statues", "iron gates"]
        settings = ["castle tower", "grand library", "moonlit garden", "candlelit ballroom", "forgotten crypt", "rose-covered gazebo", "shadowy corridor", "ornate chapel"]
        
        aesthetic = f"A {random.choice(adjectives)} scene of {random.choice(nouns)} in a {random.choice(settings)}, where {random.choice(adjectives)} shadows dance with {random.choice(adjectives)} light."
        
        embed = await self.bot.create_embed(
            "🎨 Gothic Aesthetic Generator",
            aesthetic
        )
        embed.set_footer(text="✨ Let thy imagination paint this Victorian scene")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='compliment')
    async def gothic_compliment(self, ctx, member: discord.Member = None):
        """Give a Gothic-style compliment"""
        target = member or ctx.author
        
        compliments = [
            "possesses the elegance of a Victorian rose in full bloom",
            "has eyes that hold the mystery of moonlit nights",
            "carries themselves with the grace of Gothic nobility",
            "speaks with the wisdom of ancient tomes",
            "radiates the ethereal beauty of candlelight",
            "embodies the romantic spirit of a Gothic hero",
            "has a soul as deep as the manor's foundations",
            "moves with the fluid grace of shadows dancing"
        ]
        
        compliment = random.choice(compliments)
        
        embed = await self.bot.create_embed(
            "🌹 Gothic Compliment",
            f"{target.mention} {compliment}."
        )
        embed.set_footer(text="💕 Spreading Victorian elegance and positivity")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='fortune')
    async def gothic_fortune(self, ctx):
        """Get a Gothic fortune reading"""
        fortunes = [
            "A mysterious stranger will enter thy life when the roses bloom again.",
            "Beware of shadows that move when no light dances.",
            "Thy next great adventure awaits beyond the iron gates.",
            "The portrait in the gallery holds secrets meant for thee.",
            "When three candles burn together, thy wish shall be granted.",
            "A letter bearing important news shall arrive before the new moon.",
            "The ancient key thou seekest lies closer than thou dost think.",
            "Thy kindness to another will return tenfold in Gothic splendor.",
            "Trust in the wisdom whispered by the evening wind.",
            "A treasure from the past will illuminate thy future path."
        ]
        
        fortune = random.choice(fortunes)
        
        embed = await self.bot.create_embed(
            "🔮 Gothic Fortune",
            f"The mystical forces of the manor reveal thy destiny..."
        )
        embed.add_field(
            name="Thy Fortune",
            value=fortune,
            inline=False
        )
        embed.set_footer(text="🌙 The future unfolds in shadows and starlight")
        
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(FunCommands(bot))
