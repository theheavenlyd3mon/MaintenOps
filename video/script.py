from manim import *
from manim_voiceover import VoiceoverScene
from manim_voiceover.services.elevenlabs import ElevenLabsService
import os, subprocess

# ── Color Palette ──
BG = "#0D1117"
PRIMARY = "#58C4DD"
PRIMARY_DIM = "#2A5A6A"
SECONDARY = "#83C167"
ACCENT = "#FF6B6B"
WARNING = "#FFD93D"
MUTED = "#888888"
WHITE = "#FFFFFF"

MONO = "Menlo"
TITLE_SIZE = 48
HEADING_SIZE = 36
BODY_SIZE = 30
LABEL_SIZE = 24
CAPTION_SIZE = 20

# ── Helper Functions ──

def get_api_key():
    """Read ElevenLabs key from senna profile .env"""
    result = subprocess.run(
        ["grep", "ELEVEN_LABS_API_KEY", "/Users/noctis/.hermes/profiles/senna/.env"],
        capture_output=True, text=True
    )
    line = result.stdout.strip()
    if "=" in line:
        return line.split("=", 1)[1].strip().strip("'\"")
    return ""


def make_service():
    """Create ElevenLabs TTS service"""
    key = get_api_key()
    if key:
        os.environ["ELEVEN_LABS_API_KEY"] = key
        os.environ["ELEVEN_API_KEY"] = key  # manim-voiceover expects this name
    return ElevenLabsService(
        voice_id="JBFqnCBsd6RMkjVDRZzb",  # Alice
        model="eleven_flash_v2_5",
        transcription_model=None,  # skip whisper — not needed for demo
    )


def issue_tile(text, color=ACCENT, pos=ORIGIN):
    """Create a maintenance issue tile"""
    bg = RoundedRectangle(
        width=4.5, height=0.6, corner_radius=0.08,
        fill_color=color, fill_opacity=0.2,
        stroke_color=color, stroke_width=1.5
    )
    label = Text(text, font_size=LABEL_SIZE, font=MONO, color=WHITE)
    label.move_to(bg.get_center())
    group = VGroup(bg, label).move_to(pos)
    return group


def card_bg(w=3.5, h=4.5, color=PRIMARY):
    """Background rectangle for cards"""
    return RoundedRectangle(
        width=w, height=h, corner_radius=0.12,
        fill_color=BG, fill_opacity=0.9,
        stroke_color=color, stroke_width=1.5,
        stroke_opacity=0.6
    )


def guardrail_check(text, color=SECONDARY):
    """A guardrail checkmark item"""
    dot = Dot(color=color, radius=0.08)
    label = Text(text, font_size=20, font=MONO, color=WHITE)
    group = VGroup(dot, label).arrange(RIGHT, buff=0.2, aligned_edge=UP)
    return group


# ════════════════════════════════════════════
# SCENE 1: The Problem
# ════════════════════════════════════════════

class Scene1_TheProblem(VoiceoverScene):
    def construct(self):
        self.set_speech_service(make_service())

        # -- Title --
        title = Text("MaintenOps", font_size=TITLE_SIZE, font=MONO, color=PRIMARY, weight=BOLD)
        tagline = Text("AI-Native Property Maintenance", font_size=LABEL_SIZE, font=MONO, color=MUTED)
        title_group = VGroup(title, tagline).arrange(DOWN, buff=0.2).move_to(UP * 2.5)

        with self.voiceover(text="A property manager handles 40+ maintenance calls a week. Each one means triaging the emergency, finding a licensed vendor, comparing quotes, checking compliance, processing payment, filing warranty claims — 30 to 40 percent of their day gone.") as tracker:
            self.play(Write(title), run_time=0.8)
            self.play(FadeIn(tagline, shift=UP * 0.2), run_time=0.5)
            self.wait(0.3)

            # -- Issue tiles piling up --
            issues = [
                ('AC broken — 87\xb0F', ACCENT),
                ('Toilet leaking', WARNING),
                ('Gas smell — kitchen', ACCENT),
                ('Water heater dead', WARNING),
                ('Roof leak — bedroom', ACCENT),
                ('Garage door stuck', WARNING),
            ]
            tiles = VGroup()
            start_y = 0.5
            for i, (txt, col) in enumerate(issues):
                t = issue_tile(txt, col, pos=LEFT * 4 + DOWN * (start_y - i * 0.7))
                tiles.add(t)
                self.play(Write(t, run_time=0.3), run_time=0.3)
                self.wait(0.15)

            self.wait(0.3)

            # -- Stats on right --
            stat1 = Text("3.2M", font_size=HEADING_SIZE, font=MONO, color=PRIMARY, weight=BOLD)
            stat1_label = Text("property managers", font_size=CAPTION_SIZE, font=MONO, color=MUTED)
            stat1g = VGroup(stat1, stat1_label).arrange(DOWN, buff=0.1).move_to(RIGHT * 3.5 + UP * 0.5)

            stat2 = Text("$120B", font_size=HEADING_SIZE, font=MONO, color=ACCENT, weight=BOLD)
            stat2_label = Text("market opportunity", font_size=CAPTION_SIZE, font=MONO, color=MUTED)
            stat2g = VGroup(stat2, stat2_label).arrange(DOWN, buff=0.1).next_to(stat1g, DOWN, buff=0.8)

            self.play(FadeIn(stat1g, scale=0.8), run_time=0.6)
            self.play(FadeIn(stat2g, scale=0.8), run_time=0.6)
            self.wait(0.3)

            # -- Question --
            question = Text("Who handles this?", font_size=BODY_SIZE, font=MONO, color=WARNING, weight=BOLD)
            question.move_to(DOWN * 2.5)
            self.play(Write(question), run_time=0.6)
            self.play(question.animate.scale(1.08), run_time=0.4)
            self.wait(0.5)

        self.play(FadeOut(Group(*self.mobjects)), run_time=0.5)
        self.wait(0.2)


# ════════════════════════════════════════════
# SCENE 2: Tenant Reports
# ════════════════════════════════════════════

class Scene2_TenantReports(VoiceoverScene):
    def construct(self):
        self.set_speech_service(make_service())

        with self.voiceover(text="Tenant reports a problem — text message or web form. AC is broken, 87 degrees, newborn in the apartment. MaintenOps creates a ticket and starts working.") as tracker:
            # -- Phone mock (left) --
            phone_frame = RoundedRectangle(
                width=2.8, height=5.2, corner_radius=0.3,
                fill_color="#1A1A2E", fill_opacity=0.9,
                stroke_color=MUTED, stroke_width=1
            )
            phone_frame.move_to(LEFT * 3.5)

            # SMS bubbles
            sms_tenant = RoundedRectangle(
                width=2.2, height=0.6, corner_radius=0.12,
                fill_color=PRIMARY_DIM, fill_opacity=0.8,
                stroke_color=PRIMARY, stroke_width=0.5
            ).move_to(phone_frame.get_center() + UP * 1.3)
            sms_label = Text("AC not working, 87\xb0\nand we have a newborn", font_size=16, font=MONO, color=WHITE)
            sms_label.move_to(sms_tenant.get_center())

            phone_title = Text("SMS", font_size=CAPTION_SIZE, font=MONO, color=MUTED)
            phone_title.next_to(phone_frame, UP, buff=0.2)

            self.play(FadeIn(phone_frame, shift=LEFT), run_time=0.5)
            self.play(Write(phone_title), run_time=0.3)
            self.play(Write(sms_tenant), Write(sms_label), run_time=0.8)
            self.wait(0.3)

            # -- Web form mock (right) --
            form_frame = RoundedRectangle(
                width=3.5, height=4.2, corner_radius=0.12,
                fill_color="#1A1A2E", fill_opacity=0.9,
                stroke_color=MUTED, stroke_width=1
            )
            form_frame.move_to(RIGHT * 3 + UP * 0.3)

            form_title_text = Text("Report Issue", font_size=20, font=MONO, color=PRIMARY, weight=BOLD)
            form_title_text.move_to(form_frame.get_center() + UP * 1.7)

            fields = [
                ("Address:", "123 Main St, SF"),
                ("Issue:", "AC not cooling"),
                ("Notes:", "87\xb0, infant in unit"),
            ]
            field_items = VGroup()
            for i, (lbl, val) in enumerate(fields):
                l = Text(lbl, font_size=16, font=MONO, color=MUTED)
                v = Text(val, font_size=16, font=MONO, color=WHITE)
                g = VGroup(l, v).arrange(DOWN, buff=0.05, aligned_edge=LEFT)
                g.move_to(form_frame.get_center() + UP * (0.8 - i * 0.8) + LEFT * 0.8)
                field_items.add(g)

            submit_btn = RoundedRectangle(
                width=1.6, height=0.4, corner_radius=0.08,
                fill_color=SECONDARY, fill_opacity=0.8,
                stroke_color=SECONDARY, stroke_width=0
            )
            submit_btn.move_to(form_frame.get_center() + DOWN * 1.5)
            submit_txt = Text("Submit", font_size=18, font=MONO, color=BG, weight=BOLD)
            submit_txt.move_to(submit_btn.get_center())

            form_title = Text("Web Form", font_size=CAPTION_SIZE, font=MONO, color=MUTED)
            form_title.next_to(form_frame, UP, buff=0.2)

            self.play(FadeIn(form_frame, shift=RIGHT), run_time=0.5)
            self.play(Write(form_title), run_time=0.3)
            for f in field_items:
                self.play(FadeIn(f, scale=0.9), run_time=0.2)
            self.play(FadeIn(submit_btn), Write(submit_txt), run_time=0.4)
            self.play(submit_btn.animate.set_fill_opacity(1.0), run_time=0.3)
            self.wait(0.2)

            # -- Both converge into agent node --
            agent_node = Circle(radius=0.6, fill_color=PRIMARY, fill_opacity=1.0, stroke_color=PRIMARY, stroke_width=0)
            agent_node.move_to(DOWN * 1.5)
            agent_label = Text("Agent", font_size=LABEL_SIZE, font=MONO, color=BG, weight=BOLD)
            agent_label.move_to(agent_node.get_center())

            arrow_left = CurvedArrow(
                start_point=phone_frame.get_right() + RIGHT * 0.3,
                end_point=agent_node.get_left() + LEFT * 0.3,
                angle=TAU / 6, color=PRIMARY, stroke_width=2
            )
            arrow_right = CurvedArrow(
                start_point=form_frame.get_left() + LEFT * 0.3,
                end_point=agent_node.get_right() + RIGHT * 0.3,
                angle=-TAU / 6, color=PRIMARY, stroke_width=2
            )

            self.play(Create(arrow_left), Create(arrow_right), run_time=0.5)
            self.play(GrowFromCenter(agent_node), Write(agent_label), run_time=0.6)

            # -- Ticket number --
            ticket = Text("Ticket: T-C768BE85", font_size=LABEL_SIZE, font=MONO, color=SECONDARY)
            ticket.next_to(agent_node, DOWN, buff=0.4)
            self.play(Write(ticket), run_time=0.5)
            self.wait(0.5)

        self.play(FadeOut(Group(*self.mobjects)), run_time=0.5)
        self.wait(0.2)


# ════════════════════════════════════════════
# SCENE 3: AI Triage + Compliance
# ════════════════════════════════════════════

class Scene3_AITriage(VoiceoverScene):
    def construct(self):
        self.set_speech_service(make_service())

        with self.voiceover(text="Nemotron 3 Ultra classifies the issue: URGENT — HVAC Technician. California habitability law gives us 24 hours. Safety instructions go to the tenant automatically.") as tracker:
            # -- Nemotron badge --
            badge = RoundedRectangle(
                width=3.2, height=0.5, corner_radius=0.25,
                fill_color=PRIMARY, fill_opacity=0.2,
                stroke_color=PRIMARY, stroke_width=1
            )
            badge.move_to(UP * 3)
            badge_text = Text("Nemotron 3 Ultra", font_size=LABEL_SIZE, font=MONO, color=PRIMARY, weight=BOLD)
            badge_text.move_to(badge.get_center())

            self.play(FadeIn(badge, scale=0.8), Write(badge_text), run_time=0.6)
            self.wait(0.2)

            # -- Left: Triage tags --
            left_panel = RoundedRectangle(
                width=4.5, height=4, corner_radius=0.1,
                fill_color="#1A1A2E", fill_opacity=0.8,
                stroke_color=MUTED, stroke_width=0.5
            )
            left_panel.move_to(LEFT * 3.5)

            left_title = Text("Triage", font_size=HEADING_SIZE, font=MONO, color=PRIMARY, weight=BOLD)
            left_title.next_to(left_panel, UP, buff=0.2)

            tags = [
                ("URGENT", ACCENT),
                ("Trade: HVAC Technician", WARNING),
                ("Safety: Move newborn", WARNING),
                ("to cool room", WARNING),
                ("Escalation: 24h deadline", ACCENT),
            ]
            tag_items = VGroup()
            for i, (txt, col) in enumerate(tags):
                t = Text(txt, font_size=CAPTION_SIZE, font=MONO, color=col)
                t.move_to(left_panel.get_center() + UP * (1.5 - i * 0.6))
                tag_items.add(t)

            self.play(FadeIn(left_panel, shift=LEFT), Write(left_title), run_time=0.4)
            for t in tag_items:
                self.play(Write(t), run_time=0.3)
                self.wait(0.1)

            # -- Right: Compliance -- habitability clock --
            right_panel = RoundedRectangle(
                width=4, height=4, corner_radius=0.1,
                fill_color="#1A1A2E", fill_opacity=0.8,
                stroke_color=MUTED, stroke_width=0.5
            )
            right_panel.move_to(RIGHT * 3.5)

            right_title = Text("Compliance", font_size=HEADING_SIZE, font=MONO, color=SECONDARY, weight=BOLD)
            right_title.next_to(right_panel, UP, buff=0.2)

            cali_txt = Text("CA — 24 HOURS", font_size=BODY_SIZE, font=MONO, color=ACCENT, weight=BOLD)
            cali_txt.move_to(right_panel.get_center() + UP * 1.0)

            # Clock circle with countdown
            clock_circle = Circle(radius=1.0, stroke_color=PRIMARY, stroke_width=3, fill_color="#1A1A2E", fill_opacity=0)
            clock_circle.move_to(right_panel.get_center() + DOWN * 0.5)
            clock_arrow = Line(
                clock_circle.get_center(),
                clock_circle.get_center() + UP * 0.9,
                color=ACCENT, stroke_width=3
            )

            self.play(FadeIn(right_panel, shift=RIGHT), Write(right_title), run_time=0.4)
            self.play(Write(cali_txt), run_time=0.4)
            self.play(Create(clock_circle), Create(clock_arrow), run_time=0.5)

            # Pulse the urgent tag
            self.play(tag_items[0].animate.set_color(YELLOW), run_time=0.2)
            self.play(tag_items[0].animate.set_color(ACCENT), run_time=0.2)
            self.wait(0.8)

        self.play(FadeOut(Group(*self.mobjects)), run_time=0.5)
        self.wait(0.2)


# ════════════════════════════════════════════
# SCENE 4: Vendor Matching + Guardrails
# ════════════════════════════════════════════

class Scene4_VendorMatching(VoiceoverScene):
    def construct(self):
        self.set_speech_service(make_service())

        with self.voiceover(text="Three vendors matched and ranked. NemoClaw guardrails verify every vendor's license, insurance, and spending limits — six safety checks in under a second. All pass. CoolTech HVAC at 850 dollars is the recommendation.") as tracker:
            # -- NemoClaw shield at top --
            shield_base = RoundedRectangle(
                width=2.8, height=0.5, corner_radius=0.25,
                fill_color=PRIMARY, fill_opacity=0.15,
                stroke_color=PRIMARY, stroke_width=1
            )
            shield_base.move_to(UP * 3)
            shield_text = Text("NemoClaw Guardrails", font_size=LABEL_SIZE, font=MONO, color=PRIMARY, weight=BOLD)
            shield_text.move_to(shield_base.get_center())

            shield_icon = Text("\u2622", font_size=30, color=PRIMARY)
            shield_icon.next_to(shield_base, LEFT, buff=0.15)

            self.play(FadeIn(shield_base, scale=0.8), Write(shield_text), Write(shield_icon), run_time=0.6)

            # -- 3 Vendor cards --
            vendors = [
                ("CoolTech HVAC", "4.9", "$850", SECONDARY),
                ("Bay Area Climate", "4.7", "$1,200", WARNING),
                ("Pacific HVAC", "4.2", "$950", MUTED),
            ]
            cards = VGroup()
            for i, (name, rating, price, col) in enumerate(vendors):
                card = card_bg(w=2.8, h=3.5, color=col)
                card.move_to(LEFT * (4 - i * 3.5) + DOWN * 0.3)

                name_t = Text(name, font_size=18, font=MONO, color=WHITE, weight=BOLD)
                name_t.move_to(card.get_center() + UP * 1.4)

                stars = Text(f"\u2605 {rating}", font_size=24, font=MONO, color=WARNING)
                stars.move_to(card.get_center() + UP * 0.7)

                price_t = Text(price, font_size=BODY_SIZE, font=MONO, color=col, weight=BOLD)
                price_t.move_to(card.get_center() + DOWN * 0.1)

                card_group = VGroup(card, name_t, stars, price_t)
                cards.add(card_group)

                self.play(FadeIn(card_group, shift=UP * 0.5), run_time=0.4)
                self.wait(0.1)

            self.wait(0.2)

            # -- Guardrail checks --
            checks = [
                "License verified",
                "Insurance active",
                "Budget check passed",
                "Emergency protocol OK",
            ]
            check_items = VGroup()
            for i, check in enumerate(checks):
                c = guardrail_check(check, SECONDARY)
                c.move_to(RIGHT * 4 + UP * (1.5 - i * 0.5))
                check_items.add(c)
                self.play(Write(c), run_time=0.3)
                self.wait(0.1)

            # -- All passed --
            passed = Text("ALL PASSED", font_size=HEADING_SIZE, font=MONO, color=SECONDARY, weight=BOLD)
            passed.next_to(check_items, DOWN, buff=0.3)

            # Flash the shield green
            self.play(
                shield_base.animate.set_stroke_color(SECONDARY),
                shield_text.animate.set_color(SECONDARY),
                Write(passed),
                run_time=0.5
            )
            self.wait(0.2)

            # -- Highlight CoolTech --
            arrow = Arrow(
                cards[0].get_right() + RIGHT * 0.3,
                cards[0].get_right(),
                color=SECONDARY, stroke_width=3
            )
            recommend = Text("Best Value", font_size=CAPTION_SIZE, font=MONO, color=SECONDARY)
            recommend.next_to(arrow, RIGHT, buff=0.1)

            self.play(Create(arrow), Write(recommend), run_time=0.4)
            self.play(cards[0][0].animate.set_stroke_color(SECONDARY).set_stroke_width(3), run_time=0.3)
            self.wait(0.6)

        self.play(FadeOut(Group(*self.mobjects)), run_time=0.5)
        self.wait(0.2)


# ════════════════════════════════════════════
# SCENE 5: Payment + Warranty
# ════════════════════════════════════════════

class Scene5_PaymentWarranty(VoiceoverScene):
    def construct(self):
        self.set_speech_service(make_service())

        with self.voiceover(text="Stripe Connect pays the vendor 824 dollars 50, platform earns 25 dollars 50 — 3 percent commission. And since the Lennox HVAC is still under manufacturer warranty, MaintenOps automatically files a claim.") as tracker:
            # -- Left: Stripe payment flow --
            stripe_panel = RoundedRectangle(
                width=5, height=3.5, corner_radius=0.1,
                fill_color="#1A1A2E", fill_opacity=0.9,
                stroke_color="#635BFF", stroke_width=1.5  # Stripe purple
            )
            stripe_panel.move_to(LEFT * 3 + UP * 0.5)

            stripe_title = Text("Stripe Connect", font_size=HEADING_SIZE, font=MONO, color="#635BFF", weight=BOLD)
            stripe_title.move_to(stripe_panel.get_center() + UP * 1.4)

            total = Text("$850.00 total", font_size=BODY_SIZE, font=MONO, color=WHITE)
            total.move_to(stripe_panel.get_center() + UP * 0.3)

            vendor_pay = Text("$824.50  \u2192 vendor", font_size=LABEL_SIZE, font=MONO, color=SECONDARY)
            vendor_pay.next_to(total, DOWN, buff=0.3, aligned_edge=LEFT)

            commission = Text("$25.50  \u2192 commission (3%)", font_size=LABEL_SIZE, font=MONO, color=ACCENT)
            commission.next_to(vendor_pay, DOWN, buff=0.2, aligned_edge=LEFT)

            stripe_badge = Text("Connected", font_size=CAPTION_SIZE, font=MONO, color=SECONDARY)
            stripe_badge.next_to(stripe_panel, DOWN, buff=0.2)

            self.play(FadeIn(stripe_panel, shift=LEFT), Write(stripe_title), run_time=0.5)
            self.play(Write(total), run_time=0.3)
            self.wait(0.2)
            self.play(Write(vendor_pay), run_time=0.3)
            self.wait(0.1)
            self.play(Write(commission), run_time=0.3)
            self.play(Write(stripe_badge), run_time=0.3)
            self.wait(0.2)

            # -- Right: Warranty document --
            warranty_panel = RoundedRectangle(
                width=4.5, height=3.5, corner_radius=0.1,
                fill_color="#1A1A2E", fill_opacity=0.9,
                stroke_color=SECONDARY, stroke_width=1
            )
            warranty_panel.move_to(RIGHT * 3.5 + UP * 0.5)

            warranty_title = Text("Warranty", font_size=HEADING_SIZE, font=MONO, color=SECONDARY, weight=BOLD)
            warranty_title.move_to(warranty_panel.get_center() + UP * 1.4)

            appliance = Text("Lennox XC20-048", font_size=LABEL_SIZE, font=MONO, color=WHITE)
            appliance.move_to(warranty_panel.get_center() + UP * 0.3)

            warranty_status = Text("Warranty: Active", font_size=LABEL_SIZE, font=MONO, color=SECONDARY)
            warranty_status.next_to(appliance, DOWN, buff=0.3, aligned_edge=LEFT)

            days_remain = Text("631 days remaining", font_size=CAPTION_SIZE, font=MONO, color=MUTED)
            days_remain.next_to(warranty_status, DOWN, buff=0.15, aligned_edge=LEFT)

            claim_filed = Text("Claim filed: cc770a41", font_size=CAPTION_SIZE, font=MONO, color=SECONDARY)
            claim_filed.next_to(warranty_panel, DOWN, buff=0.2)

            self.play(FadeIn(warranty_panel, shift=RIGHT), Write(warranty_title), run_time=0.5)
            self.play(Write(appliance), run_time=0.3)
            self.play(Write(warranty_status), Write(days_remain), run_time=0.4)
            self.play(Write(claim_filed), run_time=0.3)

            # -- Both highlight green --
            left_mark = Text("\u2713", font_size=48, font=MONO, color=SECONDARY)
            left_mark.next_to(stripe_panel, UP, buff=0.1)
            right_mark = Text("\u2713", font_size=48, font=MONO, color=SECONDARY)
            right_mark.next_to(warranty_panel, UP, buff=0.1)

            self.play(
                Write(left_mark), Write(right_mark),
                stripe_panel.animate.set_stroke_color(SECONDARY),
                warranty_panel.animate.set_stroke_color(SECONDARY),
                run_time=0.5
            )
            self.wait(0.6)

        self.play(FadeOut(Group(*self.mobjects)), run_time=0.5)
        self.wait(0.2)


# ════════════════════════════════════════════
# SCENE 6: The Result
# ════════════════════════════════════════════

class Scene6_TheResult(VoiceoverScene):
    def construct(self):
        self.set_speech_service(make_service())

        with self.voiceover(text="One report. 10 phases. 0.5 seconds. 850 dollars repair handled, 25 dollars 50 commission earned, warranty claim filed automatically. MaintenOps — AI-native property maintenance, built with NVIDIA Nemotron, Stripe Connect, and Hermes Agent.") as tracker:
            # -- Summary card --
            card = RoundedRectangle(
                width=7, height=5, corner_radius=0.15,
                fill_color="#1A1A2E", fill_opacity=0.95,
                stroke_color=PRIMARY, stroke_width=2
            )

            card_title = Text("Task Complete", font_size=HEADING_SIZE, font=MONO, color=PRIMARY, weight=BOLD)
            card_title.move_to(card.get_center() + UP * 2.0)

            self.play(FadeIn(card, scale=0.9), Write(card_title), run_time=0.6)
            self.wait(0.2)

            # -- 10 phase indicators left to right --
            phases = [
                "Triage", "Compliance", "Vendors", "Quotes", "Guardrails",
                "Dispatch", "Work", "Payment", "Warranty", "Complete",
            ]
            phase_groups = VGroup()
            for i, phase in enumerate(phases):
                if i < 5:
                    x = -3.0 + i * 1.3
                    y = 0.5
                else:
                    x = -3.0 + (i - 5) * 1.3
                    y = -0.5

                dot = Dot(radius=0.1, color=MUTED)
                dot.move_to(card.get_center() + RIGHT * x + UP * y)

                label = Text(phase, font_size=14, font=MONO, color=MUTED)
                label.next_to(dot, DOWN, buff=0.08)

                phase_g = VGroup(dot, label)
                phase_groups.add(phase_g)

            for pg in phase_groups:
                self.play(
                    pg[0].animate.set_color(SECONDARY).scale(2),
                    pg[1].animate.set_color(WHITE),
                    run_time=0.15
                )
                self.wait(0.05)

            # All done - set green
            for pg in phase_groups:
                pg[0].set_color(SECONDARY)
                pg[1].set_color(WHITE)

            self.wait(0.2)

            # -- Stats at bottom --
            stats_line = Text(
                "0.5 seconds  |  $25.50 earned  |  1 warranty claim",
                font_size=LABEL_SIZE, font=MONO, color=SECONDARY
            )
            stats_line.next_to(card, DOWN, buff=0.3)

            self.play(Write(stats_line), run_time=0.6)
            self.wait(0.3)

            # -- Logo + Built with --
            logo = Text("MaintenOps", font_size=TITLE_SIZE, font=MONO, color=PRIMARY, weight=BOLD)
            logo.next_to(stats_line, DOWN, buff=0.5)

            built_with = Text(
                "Built with NVIDIA Nemotron \u00b7 Stripe Connect \u00b7 Hermes Agent",
                font_size=18, font=MONO, color=MUTED
            )
            built_with.next_to(logo, DOWN, buff=0.15)

            self.play(Write(logo), run_time=0.5)
            self.play(Write(built_with), run_time=0.5)
            self.wait(1.0)

        self.play(FadeOut(Group(*self.mobjects)), run_time=0.5)
        self.wait(0.2)
