# Open questions public data cannot settle

For someone who knows thermal storage.

Framed to be answerable from general knowledge of how these systems work.
Nothing here needs internal, customer-specific or unpublished information; if a
question can only be answered with something confidential, the right answer is
"can't say," and it won't hold the work up.

## What the project is

A small independent analysis, built entirely from public data, comparing what a
thermal battery would have paid for electricity in 2025 against what an ordinary
industrial factory paid — in Spain, South Australia, and Minnesota (MISO).

The model is a pretend factory needing 10 MW of heat continuously, and a pretend
thermal battery that stores heat so it can buy power in cheap hours instead.
Real published hourly prices, real published network tariffs.

Five assumptions in it can't be checked against public sources. They're below,
roughly in order of how much turns on them.

---

## 1. What is the thing being compared against?

**What I assumed.** The comparison is *a factory that buys electricity as it
uses it* versus *a thermal battery that buys electricity when it's cheap*. Both
end up delivering identical heat. That isolates one thing: the value of being
able to choose *when* you buy.

**Why I'm unsure.** A customer switching to a thermal battery is presumably
coming off a **gas boiler**, not off inflexible electric heating. So the real
commercial comparison might be electricity-versus-gas, which is a different
question with a different answer.

**The question.** When the team frames the value of the product, what's the
reference point — the cost of heat from gas, or the cost of the same heat bought
inflexibly from the grid? Is there a standard baseline used internally?

**Why it matters.** Both are legitimate, but they answer different questions. If
the team thinks in gas terms, I should say explicitly that I'm measuring
something narrower — the value of flexibility alone — rather than letting it
read as a claim about competitiveness.

---

## 2. How fast can it charge, relative to how fast it discharges?

**What I assumed.** The battery can draw **4 to 6 times** its average power while
charging. So a system delivering 10 MW of heat around the clock might pull 40–60
MW during the hours it chooses to charge.

**Why it matters — this is the assumption the whole result rests on.** Network
operators bill a large part of the connection charge on your *peak* draw. A
battery that pulls 6× its average pays for a connection 6× larger than a normal
factory, for the same annual energy. In the Minnesota case, this single ratio is
the difference between the battery saving money and losing money.

**The question.** Is 4–6× the right order of magnitude, or is it closer to 2–3×?
And is that ratio set by the electrical side (transformer, connection), or by how
fast the blocks can physically absorb heat?

---

## 3. How many hours of storage is a normal design point?

**What I assumed.** A tank holding **12 hours** of the factory's heat — enough to
run for half a day with no charging. I also tested 4, 8, 24 and 48 hours.

**What I found.** The benefit rises steeply up to about 12 hours, then flattens
hard: going from 12 to 24 hours adds a useful amount, and 24 to 48 adds almost
nothing.

**The question.** Does that shape match how the team thinks about sizing? Is
there a typical duration these get designed around, and is it set by the
economics or by something physical?

---

## 4. Roughly how much heat leaks out while it's stored?

**What I assumed.** Originally none, which was wrong, so I added it and tested a
range. It turns out not to matter much: at 1% lost per day the answer moves by
0.2 percentage points, and even at an implausible 10% per day it costs under two
points. The reason is that the battery holds heat for *hours*, not days.

**The question.** Just the order of magnitude — is the real standby loss
comfortably under a few percent per day? I only need enough to say "negligible
at any realistic rate" with confidence rather than as an assumption.

---

## 5. What voltage does an installation this size connect at?

**What I assumed.** For Spain I used the tariff for connections at 1–30 kV. For
South Australia I used the "sub-transmission" tariff, which covers 33 and 66 kV.

**Why it matters — this is the biggest remaining risk in the analysis.** Network
tariffs are entirely determined by connection voltage, and above a certain level
you stop being a customer of the *distribution* company altogether and connect
directly to the *transmission* network, under a completely different set of
charges. If a 25–60 MW installation connects at transmission level in Australia,
then the tariff my Australian result is built on may not apply to it at all.

**The question.** For an installation in the 25–60 MW range, what voltage class
does it typically connect at? Distribution-level (roughly 11–33 kV), or straight
into transmission (66 kV and above)?

---

## 6. How binding is pairing the load to one named generator?

**Context — all public.** Otter Tail's Thermal Market Energy Pricing tariff
(Section 14.16, approved by the Minnesota PUC in November 2025) requires the
customer's load to "take service coincident with and not to exceed the hourly
generating output of a nearby specifically identified wind and/or solar
generation resource."

So the battery may only charge when one named wind farm is generating, and only
up to what it's producing that hour.

**The question.** Conceptually, how much of a constraint is that in practice,
compared with simply charging whenever power is cheap? Do the cheap hours and
that wind farm's output largely coincide anyway — or does tying to a single
generator meaningfully cut the hours available?

**Why it matters.** I haven't modelled this constraint, so my Minnesota numbers
are an upper bound. Knowing whether it's a small haircut or a large one tells me
how loudly to caveat them.

---

*Nothing above needs numbers from any real project. General principles, typical
design ranges, and "that's roughly right" or "no, it's more like X" are all
useful.*
