---
documentclass: article
geometry: margin=0.5in
fontsize: 11pt
title: Research Review - Search and Planning
---

\vspace{-2cm}

# General Problem Solver

General Problem Solver (GPS) (@gps) has been one of the most influential search program in the field of AI. From a set of clauses, the program can model a search space and apply actions based on their preconditions. Most of these concepts are similar to the methods that we developed in our planning project.

At its inception, the program was supposed to open an new era of intelligent machines. Because the approach decouples problem descriptions from solving executions, any problem could potentially be formulated and solved through a common mechanism. However, the program suffered from several limitations (@aicl). For example, the program was lacking descriptive power and recognized as a NP-Hard problem, limiting its general usage and scalability. Through the history of AI, these issues have become a common denominator of many ideas.

Historically, we can highlight the initial ambition of the project and the inspiration it had on its descendants. The first major planning system, STRIPS (@strips), has been modeled based on this paradigm. Moreover, recent cognitive architectures, such as SOAR (@soar), were also inspired by this approach.

# Backtracking and Interleaving

Backtracking and interleaving are essential techniques for programmers and computer scientists (@art, @sicp). Coupled with search algorithms, backtracking can keep track of explored states and resume the search at a valid checkpoint. On the other hand, interleaving allows the exploration of different plans, alternating their order to avoid infinite branches. Some concepts behind these techniques, such as continuations and streams (@sicp), have also been influential on their own.

One of the most well known implementation of these concepts is the Prolog language (@prolog). Compared to imperative languages, Prolog is a logic language that describes problems in term of declarative statements. Instead of a sequence of explicit steps that the program must follow, declarative programs require logical clauses that can be processed by a solving engine. Compared to GPS, first-order logic provides more descriptive power.

We can note that Prolog was inspired by an important family of languages for AI called Planner (@planner). The language has supported the creation of other major planning systems such as WARPLAN (@warplan). Today, the language is still used in state-of-the-art AI systems like IBM Watson (@watson).


# Beyond Logicial Programming: Relationnal Programming

The notion of algorithm can be captured by the following slogan: Algorithm = Logic + Control (@algorithm). Thus, a logicial program has to avoid direct control over its flow to express a problem using only logical statements. This limitation can be a great constraint for programmers accustomed to control the flow of their program. Nethertheless, it opens the way to new types of interesting programming paradigm that can exploit this capacity.

Recently, relationnal languages such as miniKaren in Scheme (@kanren) or core.logic in Clojure (@logic), have attracted the curiosity of the developer community. With this languages, plannings and searches can be formulated in a bidirectional manner (@scheme). For instance, a relational program could either solve a Sudoku problem or generate all the possible grid. I think this paradigm could lead the community to new research opportunities.

# References
