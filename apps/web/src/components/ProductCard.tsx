import { ExternalLink, Heart, Star, Target } from "lucide-react";

import type { Favorite, Offer } from "../types";
import { formatPrice } from "../utils/format";
import { ScoreBadge } from "./ScoreBadge";

type Props = {
  offer: Offer | Favorite;
  onFavorite?: (offerId: string) => void;
  onTrack?: (offerId: string) => void;
  favoriteLabel?: string;
};

function isOffer(value: Offer | Favorite): value is Offer {
  return "scoreReasons" in value;
}

export function ProductCard({ offer, onFavorite, onTrack, favoriteLabel = "В избранное" }: Props) {
  const fullOffer = isOffer(offer) ? offer : null;

  return (
    <article className="grid gap-4 rounded-lg border border-slate-200 bg-white p-4 shadow-soft dark:border-slate-800 dark:bg-slate-900 md:grid-cols-[160px_1fr_auto]">
      <div className="aspect-[4/3] overflow-hidden rounded-md bg-slate-100 dark:bg-slate-800">
        {offer.imageUrl ? (
          <img alt="" className="h-full w-full object-cover" src={offer.imageUrl} />
        ) : (
          <div className="grid h-full place-items-center text-xs text-slate-400">no image</div>
        )}
      </div>

      <div className="min-w-0">
        <div className="mb-2 flex flex-wrap items-center gap-2">
          <span className="rounded-md bg-slate-100 px-2 py-1 text-xs font-medium uppercase text-slate-600 dark:bg-slate-800 dark:text-slate-300">
            {offer.marketplace}
          </span>
          {offer.rating ? (
            <span className="inline-flex items-center gap-1 text-sm text-amber-600">
              <Star size={15} fill="currentColor" />
              {offer.rating}
            </span>
          ) : null}
        </div>
        <h2 className="line-clamp-2 text-base font-semibold leading-6">{offer.title}</h2>
        <div className="mt-3 flex flex-wrap items-end gap-2">
          <span className="text-2xl font-semibold">{formatPrice(offer.price)}</span>
          {fullOffer?.oldPrice ? (
            <span className="pb-1 text-sm text-slate-400 line-through">{formatPrice(fullOffer.oldPrice)}</span>
          ) : null}
          {fullOffer?.discountPercent ? (
            <span className="mb-1 rounded-md bg-amber-100 px-2 py-0.5 text-xs font-semibold text-amber-800 dark:bg-amber-950 dark:text-amber-200">
              -{fullOffer.discountPercent}%
            </span>
          ) : null}
        </div>
        <div className="mt-2 text-sm text-slate-500 dark:text-slate-400">
          {fullOffer?.reviewsCount ? `${fullOffer.reviewsCount.toLocaleString("ru-RU")} отзывов` : "Отзывы не указаны"}
          {fullOffer?.sellerName ? ` · ${fullOffer.sellerName}` : ""}
        </div>

        {fullOffer ? (
          <ul className="mt-3 flex flex-wrap gap-2">
            {fullOffer.scoreReasons.map((reason) => (
              <li
                key={reason}
                className="rounded-md border border-slate-200 px-2 py-1 text-xs text-slate-600 dark:border-slate-700 dark:text-slate-300"
              >
                {reason}
              </li>
            ))}
          </ul>
        ) : null}
      </div>

      <div className="flex flex-row items-center justify-between gap-3 md:flex-col md:items-end">
        {"score" in offer && typeof offer.score === "number" ? <ScoreBadge score={offer.score} /> : null}
        <div className="flex gap-2">
          {onFavorite && isOffer(offer) ? (
            <button className="icon-button" onClick={() => onFavorite(offer.id)} title={favoriteLabel} type="button">
              <Heart size={18} />
            </button>
          ) : null}
          {onTrack && isOffer(offer) ? (
            <button className="icon-button" onClick={() => onTrack(offer.id)} title="Отслеживать цену" type="button">
              <Target size={18} />
            </button>
          ) : null}
          <a className="icon-button" href={offer.productUrl} rel="noreferrer" target="_blank" title="Открыть товар">
            <ExternalLink size={18} />
          </a>
        </div>
      </div>
    </article>
  );
}
