# The GM's request, verbatim

2026-08-29, following features 201 and 202. Voice-dictated in places; "light cell" is Lightsail.

## Why

> My players are asking for a call and response. from this app specifically and it's Discord
> integration. So I think we need to update its permissions to be able to respond to messages when
> it is paged. For example, a player just posted
>
> > @L7R GM Assistant What is your purpose?

> my players and friends can get the jokes that they appear to crave.

## Where it runs, and why not fly.io

> As it happens, I have an AWS Lightsail server, which is always on. This server is not beefy enough
> to actually run the Python stuff that we are developing here. Or, actually, it probably is, to be
> honest, but I would rather keep running on fly dot i o. The fact that the light cell server is a
> five dollar per month server probably is still big enough that we could make what we're doing
> work, but I think it would be better to keep my actual code on fly dot i o because we have just
> good deployment infrastructure.

> I don't remember how much it costs to leave something running on fly dot i o all the time. I think
> it's, like, three dollars and fifty cents per month, but even that is a little bit too much to
> spend on something that is basically a joke.

> Since I already have that server running, then we don't need to spend any more money than we were
> already spending in order to have an always on server listening.

## Both bots must answer

> So what if I wanted people to be able to message either bot? the reason why I bring this up as a
> possibility is that it is a feature of good user interface design that a computer program works
> the way that its users will intuitively expect it to work. So if my players find that they are
> able to send messages to a single bot and then get responses, then they will intuitively expect
> that they can send messages to the other bot as well and get responses.

> presumably the open WebSocket connection means that we are at all times ingesting all of the
> messages that are coming into these particular Discord channels. Is that correct? and therefore we
> can program whatever specific things we respond to. Is that right?

## Testing before going live

> Yes. I'm aware that I have not added my character sheet bot to the real server yet. I wanted to do
> more testing before implementing that. I will do that when the time comes because I know that the
> moment that I add the character sheet bot there, that it would start getting talked to and used.
> So I wanted to make sure that this is all tested before I go live with it.

> What needs to change for me to test all of this out in robot role call prior to adding L7R
> Character Sheet to the real server.

## On the permission change, and whether the bot must be re-added

> I think I will need to make some changes to the permissions of the GM Assistant bot I because
> currently, we designed it without any notion that it could read messages. I don't know what that
> means as far as it already being present in the existing Discord servers. Like, if I need to drop
> and then re add it or something. because I'm sure that you cannot simply add a bot to a server,
> and then after it has been added, increase its permissions.

> Hopefully, I don't have to drop it and re add it in a way that will be visible to everyone simply
> because I don't want to trouble people by showing them all of the various tweaks I'm doing because
> that will show up as, like, unread messages that they will feel like they have to look at. But if
> that is what is required for visibility, for permission reasons to prevent bad factors from
> escalating privileges without people's knowledge, then that's fine.

## On conforming to Discord's expectations

> I definitely want to conform to however Discord expects that bots will work because I don't want
> to accidentally do something that would be against Discord's terms of service.

## Earlier, on the loop hazard (2026-08-28)

> someone immediately mentioned cake and then said that the bot should autorespond to any mention of
> cake with reply saying that the cake is a lie. I counted that we did something like this at work,
> and then the bot was carelessly programmed, so it just kept responding to itself in an infinite
> loop that was really bad for the server and made it unusable. I said that I would think about
> implementing that kind of feature in the future, and that I would try to avoid making the same
> mistake, but that I couldn't make any promises.
