import discord
from discord.ext import commands
from datetime import datetime
import config

class ApplicationCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='apply')
    async def submit_application(self, ctx, *, application_type=None):
        """Submit an application"""
        if not application_type:
            embed = await self.bot.create_embed(
                "Application Types",
                "Available applications in our Gothic manor:"
            )
            embed.add_field(
                name="📜 Available Types",
                value="• `staff` - Join our Gothic staff\n• `moderator` - Become a guardian of order\n• `helper` - Assist fellow manor residents\n• `artist` - Share thy creative talents\n• `writer` - Contribute to our lore",
                inline=False
            )
            embed.add_field(
                name="Usage",
                value=f"`{ctx.prefix}apply <type>`",
                inline=False
            )
            await ctx.send(embed=embed)
            return
        
        # Check if user already has pending application
        existing = await self.bot.db_service.get_user_application(ctx.author.id, ctx.guild.id, application_type)
        if existing and existing.status == 'pending':
            embed = await self.bot.create_embed(
                "Existing Application",
                f"Thou already hast a pending {application_type} application. Please wait for review."
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        # Start application process
        embed = await self.bot.create_embed(
            f"🏛️ {application_type.title()} Application",
            f"Greetings, {ctx.author.mention}! Thou hast chosen to apply for the noble position of **{application_type}**."
        )
        embed.add_field(
            name="📝 Process",
            value="I shall send thee a series of questions via direct message. Please answer them thoughtfully.",
            inline=False
        )
        
        await ctx.send(embed=embed)
        
        # Get application questions
        questions = self.get_application_questions(application_type)
        
        # Send DM with application
        try:
            dm_embed = await self.bot.create_embed(
                f"🏛️ {application_type.title()} Application for {ctx.guild.name}",
                "Welcome to the Gothic application process! Please answer each question thoroughly."
            )
            await ctx.author.send(embed=dm_embed)
            
            responses = {}
            
            for i, question in enumerate(questions, 1):
                question_embed = await self.bot.create_embed(
                    f"Question {i}/{len(questions)}",
                    question
                )
                await ctx.author.send(embed=question_embed)
                
                # Wait for response
                def check(message):
                    return message.author == ctx.author and isinstance(message.channel, discord.DMChannel)
                
                try:
                    response = await self.bot.wait_for('message', timeout=300.0, check=check)
                    responses[question] = response.content
                    
                    # Confirm response
                    confirm_embed = await self.bot.create_embed(
                        "Response Recorded",
                        f"✅ Response recorded: {response.content[:100]}{'...' if len(response.content) > 100 else ''}"
                    )
                    await ctx.author.send(embed=confirm_embed)
                    
                except asyncio.TimeoutError:
                    timeout_embed = await self.bot.create_embed(
                        "Application Timeout",
                        "Thy application has timed out. Please start over when ready."
                    )
                    await ctx.author.send(embed=timeout_embed)
                    return
            
            # Save application
            application = await self.bot.db_service.create_application(
                ctx.guild.id, ctx.author.id, application_type, responses
            )
            
            if application:
                # Send confirmation
                final_embed = await self.bot.create_embed(
                    "Application Submitted",
                    f"Thy {application_type} application has been submitted to the Gothic council for review."
                )
                final_embed.add_field(
                    name="Application ID",
                    value=f"#{application.id}",
                    inline=True
                )
                final_embed.add_field(
                    name="Status",
                    value="Pending Review",
                    inline=True
                )
                final_embed.add_field(
                    name="Next Steps",
                    value="The Gothic council will review thy application and contact thee with their decision.",
                    inline=False
                )
                
                await ctx.author.send(embed=final_embed)
                
                # Notify staff
                guild_config = await self.bot.db_service.get_guild_config(ctx.guild.id)
                if guild_config and guild_config.staff_channel:
                    staff_channel = self.bot.get_channel(int(guild_config.staff_channel))
                    if staff_channel:
                        staff_embed = await self.bot.create_embed(
                            "🏛️ New Application Received",
                            f"A new {application_type} application has been submitted!"
                        )
                        staff_embed.add_field(
                            name="Applicant",
                            value=f"{ctx.author.mention} ({ctx.author})",
                            inline=True
                        )
                        staff_embed.add_field(
                            name="Application ID",
                            value=f"#{application.id}",
                            inline=True
                        )
                        staff_embed.add_field(
                            name="Type",
                            value=application_type.title(),
                            inline=True
                        )
                        staff_embed.add_field(
                            name="Review Commands",
                            value=f"`{ctx.prefix}review {application.id}`\n`{ctx.prefix}approve {application.id}`\n`{ctx.prefix}reject {application.id}`",
                            inline=False
                        )
                        
                        await staff_channel.send(embed=staff_embed)
                
                await self.bot.log_action(ctx.guild.id, ctx.author.id, 'application_submit', {
                    'application_id': application.id,
                    'type': application_type
                })
            
        except discord.Forbidden:
            embed = await self.bot.create_embed(
                "DM Blocked",
                "I cannot send thee direct messages. Please enable DMs from server members and try again."
            )
            await ctx.send(embed=embed, delete_after=10)
    
    def get_application_questions(self, app_type):
        """Get questions for application type"""
        base_questions = [
            "What is thy Discord name and how long hast thou been using Discord?",
            "How long hast thou been a member of this Gothic manor?",
            "What timezone art thou in and when art thou most active?",
            "Why dost thou wish to join our Gothic staff?"
        ]
        
        type_questions = {
            'staff': [
                "What previous moderation or staff experience dost thou possess?",
                "How wouldst thou handle a conflict between two members?",
                "What unique skills or perspectives canst thou bring to our staff?"
            ],
            'moderator': [
                "Describe thy experience with Discord moderation and bot usage.",
                "How wouldst thou handle spam, toxicity, or rule violations?",
                "What is thy philosophy on fair and effective moderation?"
            ],
            'helper': [
                "How dost thou prefer to assist other community members?",
                "What subjects or areas art thou most knowledgeable about?",
                "Describe a time when thou helped someone overcome a problem."
            ],
            'artist': [
                "What types of art dost thou create (digital, traditional, etc.)?",
                "Share links to thy portfolio or examples of thy Gothic-themed work.",
                "How wouldst thou contribute to our manor's visual identity?"
            ],
            'writer': [
                "What writing experience dost thou possess?",
                "Share examples of thy writing, preferably Gothic or Victorian themed.",
                "How wouldst thou contribute to our manor's lore and storytelling?"
            ]
        }
        
        return base_questions + type_questions.get(app_type, [])
    
    @commands.command(name='applications', aliases=['apps'])
    @commands.has_permissions(manage_guild=True)
    async def list_applications(self, ctx, status="pending"):
        """List applications by status"""
        applications = await self.bot.db_service.get_applications_by_status(ctx.guild.id, status)
        
        if not applications:
            embed = await self.bot.create_embed(
                f"No {status.title()} Applications",
                f"There are no {status} applications in our Gothic archives."
            )
            await ctx.send(embed=embed)
            return
        
        embed = await self.bot.create_embed(
            f"🏛️ {status.title()} Applications",
            f"Found {len(applications)} {status} applications."
        )
        
        for app in applications[:10]:  # Show first 10
            user = ctx.guild.get_member(int(app.user.discord_id))
            user_name = user.display_name if user else app.user.username
            
            embed.add_field(
                name=f"Application #{app.id}",
                value=f"**Type:** {app.type.title()}\n**Applicant:** {user_name}\n**Submitted:** {app.created_at.strftime('%Y-%m-%d')}",
                inline=True
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='review')
    @commands.has_permissions(manage_guild=True)
    async def review_application(self, ctx, application_id: int):
        """Review a specific application"""
        application = await self.bot.db_service.get_application_by_id(application_id)
        
        if not application:
            embed = await self.bot.create_embed(
                "Application Not Found",
                f"Application #{application_id} does not exist in our Gothic records."
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        user = ctx.guild.get_member(int(application.user.discord_id))
        user_name = user.display_name if user else application.user.username
        
        embed = await self.bot.create_embed(
            f"🏛️ Application Review #{application.id}",
            f"Detailed review of {application.type} application"
        )
        embed.add_field(
            name="📋 Application Details",
            value=f"**Type:** {application.type.title()}\n**Applicant:** {user_name}\n**Status:** {application.status.title()}\n**Submitted:** {application.created_at.strftime('%Y-%m-%d %H:%M UTC')}",
            inline=False
        )
        
        # Show responses
        if application.responses:
            for i, (question, answer) in enumerate(application.responses.items(), 1):
                embed.add_field(
                    name=f"Q{i}: {question[:50]}{'...' if len(question) > 50 else ''}",
                    value=answer[:200] + ('...' if len(answer) > 200 else ''),
                    inline=False
                )
        
        embed.add_field(
            name="🔧 Actions",
            value=f"`{ctx.prefix}approve {application.id}` - Approve application\n`{ctx.prefix}reject {application.id} <reason>` - Reject application",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='approve')
    @commands.has_permissions(manage_guild=True)
    async def approve_application(self, ctx, application_id: int, *, note=None):
        """Approve an application"""
        application = await self.bot.db_service.get_application_by_id(application_id)
        
        if not application:
            embed = await self.bot.create_embed(
                "Application Not Found",
                f"Application #{application_id} does not exist in our Gothic records."
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        if application.status != 'pending':
            embed = await self.bot.create_embed(
                "Application Already Processed",
                f"Application #{application_id} has already been {application.status}."
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        # Update application status
        await self.bot.db_service.update_application_status(
            application_id, 'approved', ctx.author.id, note
        )
        
        # Send confirmation
        embed = await self.bot.create_embed(
            "✅ Application Approved",
            f"Application #{application_id} for {application.type} has been approved!"
        )
        embed.add_field(
            name="Approved By",
            value=ctx.author.mention,
            inline=True
        )
        if note:
            embed.add_field(
                name="Note",
                value=note,
                inline=False
            )
        
        await ctx.send(embed=embed)
        
        # Notify applicant
        user = ctx.guild.get_member(int(application.user.discord_id))
        if user:
            try:
                dm_embed = await self.bot.create_embed(
                    "🎉 Application Approved!",
                    f"Congratulations! Thy {application.type} application for **{ctx.guild.name}** has been approved!"
                )
                dm_embed.add_field(
                    name="Next Steps",
                    value="Please contact the staff team for onboarding and role assignment.",
                    inline=False
                )
                if note:
                    dm_embed.add_field(
                        name="Staff Note",
                        value=note,
                        inline=False
                    )
                
                await user.send(embed=dm_embed)
            except discord.Forbidden:
                pass
        
        await self.bot.log_action(ctx.guild.id, ctx.author.id, 'application_approve', {
            'application_id': application_id,
            'type': application.type,
            'note': note
        })
    
    @commands.command(name='reject')
    @commands.has_permissions(manage_guild=True)
    async def reject_application(self, ctx, application_id: int, *, reason="No reason provided"):
        """Reject an application"""
        application = await self.bot.db_service.get_application_by_id(application_id)
        
        if not application:
            embed = await self.bot.create_embed(
                "Application Not Found",
                f"Application #{application_id} does not exist in our Gothic records."
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        if application.status != 'pending':
            embed = await self.bot.create_embed(
                "Application Already Processed",
                f"Application #{application_id} has already been {application.status}."
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        # Update application status
        await self.bot.db_service.update_application_status(
            application_id, 'rejected', ctx.author.id, reason
        )
        
        # Send confirmation
        embed = await self.bot.create_embed(
            "❌ Application Rejected",
            f"Application #{application_id} for {application.type} has been rejected."
        )
        embed.add_field(
            name="Rejected By",
            value=ctx.author.mention,
            inline=True
        )
        embed.add_field(
            name="Reason",
            value=reason,
            inline=False
        )
        
        await ctx.send(embed=embed)
        
        # Notify applicant
        user = ctx.guild.get_member(int(application.user.discord_id))
        if user:
            try:
                dm_embed = await self.bot.create_embed(
                    "Application Update",
                    f"Unfortunately, thy {application.type} application for **{ctx.guild.name}** has been declined."
                )
                dm_embed.add_field(
                    name="Reason",
                    value=reason,
                    inline=False
                )
                dm_embed.add_field(
                    name="Reapplication",
                    value="Thou may apply again in the future after addressing the concerns mentioned.",
                    inline=False
                )
                
                await user.send(embed=dm_embed)
            except discord.Forbidden:
                pass
        
        await self.bot.log_action(ctx.guild.id, ctx.author.id, 'application_reject', {
            'application_id': application_id,
            'type': application.type,
            'reason': reason
        })

def setup(bot):
    bot.add_cog(ApplicationCommands(bot))
