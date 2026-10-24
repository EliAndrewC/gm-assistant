# Feature 222 - the GM's request, verbatim

Dictated 2026-10-24, in three messages. Substitutions read silently per the user-level transcription table: "Haiku" =
koku (every occurrence), "Rakugani" = Rokugani.

## Message 1

> I would like to reprice the basket of goods for modern prices, because saying $550 in 2017 dollars is not really helpful considering how much inflation has happened since then. Can you, like, are you able to do those calculations? I don't even think you need the diagram repo for that, right? That feels like something you can probably do on your own, and in fact, I think that instead of just doing a one-off recomputation, we probably want some kind of scripted or automated process that we are able to just kind of update. And also, I guess if that process was extensible, like if we decided to change the basket of goods or even to run it for different baskets of goods to say things like, hey, how much does it move the numbers if you count this other thing? that kind of thing. To be honest, I think I would love to have a tool on our GM Assistant website that is the how much is a Haiku worth tool that lets you play with that and kind of add or remove things from the basket to kind of indicate what a Haiku is worth. I think that would be really fun. In fact, I think I do want to create a money section of the site, and I think this should be the first thing that we put there. Though I do want there to be other things on the money section of the site. What do you think of that? Is this enough direction for you to throw something together, or should we talk more about what the requirements are and how it should work?

## Session reply (summary)

Proposed: a `reprice` command writing dated snapshots priced by a session at bulk retail with a link per good; a
2026 pricing; a Money section whose first tool is "What's a koku worth?" (toggle goods, edit quantities, swap
substitutes, add a custom good, live PPP with each good's share, the second reading beside it, reset, state in the URL);
named alternate baskets. BLS average prices recommended only as a cross-check.

## Message 2

> I actually do think that I would like to have the diagram skill do some of that research, because I think that's something that I'm going to want in the diagram research, is that we have a lot of places where we list historical prices. So for example, the page that I happen to have open right now says
>
> > At Takamiya, on the Nakasendo, the station's statement of the same year gives three fares for the 1.5 ri to Toriimoto, 40, 27 and 20 mon, which by their proportions this project reads as a pack horse, a light horse and a porter: about 27, 18 and 13 mon a ri.
>
> Now that's really great information. But I think this is a case where I am probably going to want a new type of tooltip where anytime we display a monetary amount, then, like, currently there is a tooltip over the actual word `mon` explaining that it is a copper coin. And that it was the lowest denomination. However, I think that I am going to want a tooltip where we don't just explain that this was the copper coin, but we translate the amount of money based on different ways of understanding it. So, for example, we could say that `20 mon` is worth:
> - $X in purchasing power parity terms
> - $Y in modern labor terms ( We should probably come up with a concise way to express this. Like, I'm not sure what term we have, but, you know, kind of as you note that Haiku translates one way in purchasing power parity dollars and then another in, like, amount of money that people get for their labor dollars)
> - some amount of Rakugani money as expressed in sen, zeni, bu, and/or koku by way of our purchasing power parity conversions
>
> So in order to do that, I think that what we need is to have some basket of goods that we have standardized on, that is our like main one, that we think is representative. And then I think that we want to try, to the maximum extent possible, to make those conversions for different time periods in the history of the places that we have researched, like Edo period Japan and, you know, whichever Chinese dynasties we have used to pull data for this and things like that. And then when we express those amounts of money, we can try to give conversions in this way. And those conversions will actually kind of make sense without just being totally hand-wavy, even if they are approximate.
>
> In order to do a good job of this, we probably do need to think about what our basket of goods contains. For example, I don't remember whether Chris thought to put salt in that basket of goods, but that might be something that needs to be there, because that is an essential thing that people need, as opposed to something like pepper, which is a seasoning which is not required to live. that kind of thing. I mean, I think Chris did a great job with the purchasing power parity analysis that he did. But in addition to updating the prices, we probably do need to think about what that basket of goods should contain. Do you feel like that's something that you can do? Because that doesn't involve, like, historical research per se. That's just like a general research question that doesn't require the specific workflows that we've developed at the diagram skill. So I think that's something you can probably do, though I will defer to you on that question, and I can create another diagram repo session for you to collaborate with as needed.

## Session reply (summary)

Proposed the split: HERE - the standard basket designed from the welfare-ratio literature (salt, fuel and housing in;
luxuries out; the 2017 basket kept as a named alternate), today's prices and the reprice command, a conversion engine
publishing a conversion table (goods dollars, wage dollars, Rokugani coin per currency, era and place), the Money section
with the playground. DIAGRAM, by GitHub issue - each era and place's basket cost in local money, coin exchange rates and
laborer wages; Kyoto 1745-54 silver prices for the new goods; and the tooltip on its own research site, which vendors
the conversion table. Proposed renaming "big deal" dollars to **wage dollars**, paired with **goods dollars**.

## Message 3

> Sounds great. Please proceed with that. Thanks.
