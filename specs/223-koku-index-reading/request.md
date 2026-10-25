# Request (the GM, 2026-10-25, verbatim; dictated)

Dictation substitutions: "cuckoo" = koku; "Koku" = koku.

## Message 1

> I am working on the money app that is on the GM Assistant website, and the calculator for what constitutes a koku
> has a pretty good user interface, But I think that the way that it is doing its calculations is fundamentally wrong
> in a way that makes me wonder whether our use of the basket of goods to calculate a cuckoo is correct or
> well-reasoned.
>
> Today, I am able to select or deselect different goods. And as far as I can tell, what those goods are doing is
> adding or removing value from the worth of a cuckoo. So for example, if I select housing as something that is taken
> into account when computing what the present day dollar amount of a cuckoo is, then I see the value shoot up
> dramatically. Because now one cuckoo is considered to be what it takes to buy all of those other things and also
> provide housing as well. But that's not the point of the calculations that we're doing. That completely
> misunderstands the conversion that we are trying to perform.
>
> Now, I suppose that this might suggest that our UI needs to be a little more complicated, because it might need to
> take different ways of calculating the value of a cuckoo (cuckoo -> koku) into account. But let me say what I mean.
> if the amount of rice that one koku is meant to represent is about 150 kilograms, And we are saying that the gold
> coin of the cuckoo is tied to that amount of rice and is notionally worth that in some way, with all of the caveats
> about market price versus government fixed price, etc. So therefore, one way to perform the conversion of what a
> cuckoo is worth is to simply ask, what does 150 kilograms of rice cost? So if I Google for that and find that it
> costs about $120, then one way to calculate the worth of a koku is to say that a koku is worth $120.
>
> However, that is only one good. And different things have gotten cheaper at different rates between the pre-modern
> world and today. Therefore, if I were to also look up what volume of soybeans could be purchased for 1 koku
> historically, and then looked up the modern price of soybeans, then I might get a very different number. The same
> thing would apply to salt, or fish or cooking oil. My guess would be, without having checked, that all of these
> things have gotten cheaper, but that fish in particular has decreased in price less than these other items. And
> therefore, if I tried to figure out the value of a koku by comparing the price of fish in pre-modern times to the
> price of fish now, then I would get an extremely different number than when trying to do that for rice. Housing is a
> far more dramatic version of this, because if we are talking about the price of materials, then those have gone
> down, but because of modern zoning laws, then in many places the price of housing has actually increased as a matter
> of labor hours required to purchase it, due to the fact that the ability to build housing on land and needing to own
> that land is a major driver of the cost.
>
> So if we are trying to compute the modern dollar amount that a koku is worth, then we would surely not add up all of
> these things together. We would be taking some kind of average, possibly a weighted average, possibly not. So for
> example, if buying 150 kilograms of rice was found to cost $120, and buying whatever the equivalent soybean amount
> was found to cost $180, then if we were using both of those as inputs for determining the price of a koku, then we
> would probably arrive at something like $150, because $150 is the average of those two numbers.
>
> Whereas the way that you have created the Koku calculation chart, you have made it so that if I take soybeans into
> account, then the price of soybeans is straightforwardly added to the modern dollar amount of a Koku. This seems bad.
>
> Now, I think there is a version of what you are doing that makes sense. And here's the version of that that I think
> has some basis in an actual real calculation. Instead of converting goods as averages, we know that there were
> things that a household needed in a given year, and we know the approximate income in Koku of these pre-modern
> households. So I think it makes sense in that context to say that if we believe that a median pre-modern household
> had this basket of goods consumed over the course of a year, and then we looked up the modern prices for that exact
> basket of goods, then that would be another way to arrive at the modern equivalent of a value of a Koku. And of
> course I have said household here, but this could also be done for a single city laborer, which might be a little
> simpler. Though in that case, I don't think it makes sense to include or exclude specific things in the way that we
> have done, because excluding things that we know that would have been used invalidates the calculation, frankly. But
> ultimately, I think that those are two different approaches to calculating the value of a koku. And I think that
> what we have done is a mixture of the two that invalidates both approaches.
>
> And of course, I have simplified things by talking about one price for the pre-modern world, but actually we are
> drawing from a number of different historical periods in our calculations and when doing our conversions. So I think
> that we will probably have some kind of weighted average of the pre-modern prices that uses the different periods
> and how representative we think they are of our setting and such. I mean, to be clear, we should do that no matter
> what.
>
> Does that make sense? What do you think about this? What do you propose that might apply these baskets of goods in a
> rigorous way? [...] So can you take a step back and then think about what these baskets of goods are actually used
> to compute when they are invoked in academic papers, and then think through how we might apply that here? Note that
> I do have a session of the diagram repo running and watching GitHub, so if you need to file more research tasks,
> then you are able to do so, but I don't want to do that just yet before we actually think through what our approach
> even should be.

## The session's answer (summarized) and its proposal

The goods-dollar koku was already a weighted average, not a sum: basket dollars over basket silver, times a koku's
silver, is identically the reference-era spending-weighted arithmetic mean of each good's single-good koku (a
Laspeyres index); with spending weights the GM's two approaches give the same number. Housing raises it because its
own reading is $4,384 against rice's $191, at 11% weight. What the GM is right about: the spread across goods ($36 to
$4,384) is the real finding and the page hid it; the toggles fit the "average over goods" reading but not the
"household's year" reading the basket is described as; and the eras were not averaged. Several modern prices compare
unlike goods (organic soybeans, specialty wheat berries, cod fillets).

Proposal:
1. Make the per-good table the core of the page (each good's single-good koku and its weight); the headline becomes a
   range with the averaging method as a documented knob: weighted arithmetic (Laspeyres) labeled the high reading,
   geometric mean or Fisher the central.
2. Split the framings: "whole basket" (the household year, fixed, no good toggles, only substitute price options) and
   "average over goods" (toggles allowed, labeled as choosing which goods enter the average).
3. Era averaging in rice terms: each era's prices expressed in kg of rice (stripping debasements and silver's own
   value), a weighted mean across eras, era weights the GM's knob.
4. Research questions to diagram: like-for-like modern goods at the matching market level, housing's comparator, era
   coverage beyond rice, which mean historians take, modern quantities for Fisher.

## Message 2

> I think your proposal is good, what you're saying makes sense, and so please proceed with that, including the filing
> of whatever research questions you need to file for the diagram session, which is currently watching and can
> respond as it completes that research. Thank you.
